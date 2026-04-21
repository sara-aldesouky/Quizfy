"""FastAPI application for full-class performance analytics."""

from __future__ import annotations

from typing import Annotated

import logging

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .models import AnalysisRequest, AnalysisResponse, ErrorResponse, UploadResponse
from .security import configure_safe_logging, redact
from .services.analyzer import PerformanceAnalyzer
from .services.excel_processor import ExcelProcessor
from .services.pdf_processor import PDFProcessor
from .services.topic_classifier import TopicClassifier
from .services.vector_store import vector_store
from .storage import store


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Quizfy Performance Analytics",
    version="1.0.0",
    description="Class-first assessment weakness analytics from PDF questions and Excel results.",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def validate_configuration() -> None:
    configure_safe_logging()
    config.validate_startup()
    vector_store.configure()
    logger.info("Performance analytics configuration validated")


@app.middleware("http")
async def log_requests_safely(request: Request, call_next):
    response = await call_next(request)
    logger.info(
        "analytics_request method=%s path=%s status=%s",
        request.method,
        request.url.path,
        response.status_code,
    )
    return response


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    logger.error(
        "analytics_runtime_error path=%s error=%s",
        request.url.path,
        redact(type(exc).__name__),
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal service configuration error"},
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "analytics_unexpected_error path=%s error=%s",
        request.url.path,
        redact(type(exc).__name__),
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "performance_analytics"}


@app.post("/upload/pdf", response_model=UploadResponse)
async def upload_pdf(
    file: Annotated[UploadFile, File(...)],
    exam_name: Annotated[str | None, Form()] = None,
    subject: Annotated[str | None, Form()] = None,
) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    content = await _read_limited_file(file)
    pdf_id = store.new_id("pdf")
    path = store.save_upload(pdf_id, file.filename, content)

    extracted = PDFProcessor().extract_questions(path, pdf_id)
    classified = TopicClassifier().classify_batch(extracted, subject=subject)
    vector_store.ingest_questions(classified)
    store.save_questions(pdf_id, classified)

    return UploadResponse(
        file_id=pdf_id,
        filename=file.filename,
        records_processed=len(classified),
        status="success",
        message=f"{len(classified)} questions extracted and classified for {exam_name or 'assessment'}.",
    )


@app.post("/upload/excel", response_model=UploadResponse)
async def upload_excel(
    file: Annotated[UploadFile, File(...)],
    class_name: Annotated[str | None, Form()] = None,
) -> UploadResponse:
    allowed = (".xlsx", ".xls", ".csv", ".tsv")
    if not file.filename or not file.filename.lower().endswith(allowed):
        raise HTTPException(status_code=400, detail="Only Excel, CSV, or TSV files are supported.")
    content = await _read_limited_file(file)
    excel_id = store.new_id("excel")
    path = store.save_upload(excel_id, file.filename, content)

    results = ExcelProcessor().normalize_results(path)
    if class_name:
        results = [
            result.model_copy(update={"class_name": result.class_name or class_name})
            for result in results
        ]
    store.save_results(excel_id, results)

    return UploadResponse(
        file_id=excel_id,
        filename=file.filename,
        records_processed=len(results),
        status="success",
        message=f"{len({result.student_id for result in results})} students and {len(results)} result rows imported.",
    )


@app.post("/analyze/class", response_model=AnalysisResponse)
def run_class_analysis(request: AnalysisRequest) -> AnalysisResponse:
    questions = store.pdf_questions.get(request.pdf_id)
    results = store.excel_results.get(request.excel_id)
    if questions is None:
        raise HTTPException(status_code=404, detail=f"Unknown pdf_id: {request.pdf_id}")
    if results is None:
        raise HTTPException(status_code=404, detail=f"Unknown excel_id: {request.excel_id}")

    analysis = PerformanceAnalyzer().analyze(request, questions, results)
    store.save_analysis(analysis)
    return analysis


@app.get("/analyze/class/summary")
def get_class_summary(
    analysis_id: Annotated[str | None, Query()] = None,
) -> dict:
    analysis = _get_analysis(analysis_id)
    return analysis.class_summary.model_dump()


@app.get("/analyze/student/{student_id}")
def get_student_summary(
    student_id: str,
    analysis_id: Annotated[str | None, Query()] = None,
) -> dict:
    analysis = _get_analysis(analysis_id)
    for summary in analysis.student_summaries:
        if summary.student_id == student_id:
            return summary.model_dump()
    raise HTTPException(status_code=404, detail=f"Student not found in analysis: {student_id}")


@app.get("/analyze/filter", response_model=AnalysisResponse)
def filter_analysis(
    pdf_id: str,
    excel_id: str,
    student_id: Annotated[list[str] | None, Query()] = None,
    class_name: str | None = None,
    min_students_affected: int = 1,
    confidence_threshold: float = 0.65,
) -> AnalysisResponse:
    return run_class_analysis(
        AnalysisRequest(
            pdf_id=pdf_id,
            excel_id=excel_id,
            filter_students=student_id,
            filter_class=class_name,
            min_students_affected=min_students_affected,
            confidence_threshold=confidence_threshold,
        )
    )


async def _read_limited_file(file: UploadFile) -> bytes:
    content = await file.read()
    max_bytes = config.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {config.MAX_FILE_SIZE_MB} MB limit.",
        )
    return content


def _get_analysis(analysis_id: str | None) -> AnalysisResponse:
    if analysis_id:
        analysis = store.analyses.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Unknown analysis_id: {analysis_id}")
        return analysis
    if not store.analyses:
        raise HTTPException(status_code=404, detail="No analysis has been run yet.")
    return next(reversed(store.analyses.values()))
