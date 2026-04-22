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
    allow_origins=["*"],  # Allow all origins for file upload from Safari
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
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
    try:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
        logger.info(f"Uploading PDF: {file.filename}")
        content = await _read_limited_file(file)
        
        logger.info(f"Processing PDF with PDFProcessor")
        pdf_id = store.new_id("pdf")
        path = store.save_upload(pdf_id, file.filename, content)

        extracted = PDFProcessor().extract_questions(path, pdf_id)
        logger.info(f"Extracted {len(extracted)} questions from PDF")
        
        logger.info(f"Classifying questions with TopicClassifier")
        classified = TopicClassifier().classify_batch(extracted, subject=subject)
        logger.info(f"Classified {len(classified)} questions")
        
        logger.info(f"Ingesting questions into vector store")
        vector_store.ingest_questions(classified)
        
        store.save_questions(pdf_id, classified)
        
        logger.info(f"PDF upload complete: {pdf_id}")
        return UploadResponse(
            file_id=pdf_id,
            filename=file.filename,
            records_processed=len(classified),
            status="success",
            message=f"{len(classified)} questions extracted and classified for {exam_name or 'assessment'}.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF upload error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(e)}"
        )


@app.post("/upload/excel", response_model=UploadResponse)
async def upload_excel(
    file: Annotated[UploadFile, File(...)],
    class_name: Annotated[str | None, Form()] = None,
) -> UploadResponse:
    try:
        allowed = (".xlsx", ".xls", ".csv", ".tsv")
        if not file.filename or not file.filename.lower().endswith(allowed):
            raise HTTPException(status_code=400, detail="Only Excel, CSV, or TSV files are supported.")
        
        logger.info(f"Uploading Excel: {file.filename}")
        content = await _read_limited_file(file)
        
        excel_id = store.new_id("excel")
        path = store.save_upload(excel_id, file.filename, content)

        logger.info(f"Processing Excel with ExcelProcessor")
        results = ExcelProcessor().normalize_results(path)
        logger.info(f"Normalized {len(results)} result rows")
        
        if class_name:
            results = [
                result.model_copy(update={"class_name": result.class_name or class_name})
                for result in results
            ]
        
        store.save_results(excel_id, results)
        
        unique_students = len({result.student_id for result in results})
        logger.info(f"Excel upload complete: {excel_id} ({unique_students} students)")
        
        return UploadResponse(
            file_id=excel_id,
            filename=file.filename,
            records_processed=len(results),
            status="success",
            message=f"{unique_students} students and {len(results)} result rows imported.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel upload error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process Excel: {str(e)}"
        )


@app.post("/analyze/class", response_model=AnalysisResponse)
def run_class_analysis(request: AnalysisRequest) -> AnalysisResponse:
    try:
        logger.info(f"Starting class analysis: pdf_id={request.pdf_id}, excel_id={request.excel_id}")
        
        questions = store.pdf_questions.get(request.pdf_id)
        results = store.excel_results.get(request.excel_id)
        
        if questions is None:
            logger.error(f"PDF not found: {request.pdf_id}")
            raise HTTPException(status_code=404, detail=f"Unknown pdf_id: {request.pdf_id}")
        if results is None:
            logger.error(f"Excel not found: {request.excel_id}")
            raise HTTPException(status_code=404, detail=f"Unknown excel_id: {request.excel_id}")

        logger.info(f"Found {len(questions)} questions and {len(results)} results")
        logger.info(f"Running PerformanceAnalyzer")
        
        analysis = PerformanceAnalyzer().analyze(request, questions, results)
        
        logger.info(f"Analysis complete: {analysis.analysis_id}")
        logger.info(f"Class weak topics: {len(analysis.class_summary.weak_topics)}")
        logger.info(f"Student summaries: {len(analysis.student_summaries)}")
        
        store.save_analysis(analysis)
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run analysis: {str(e)}"
        )


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
