"""Small storage abstraction for uploaded artifacts and analysis results."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import config
from .models import AnalysisResponse, ClassifiedQuestion, StudentResult


class AnalyticsStore:
    """In-process store with JSON snapshots for easy service integration.

    This keeps the first version simple while preserving a clean boundary for a
    future database-backed implementation.
    """

    def __init__(self) -> None:
        self.upload_dir = Path(config.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_questions: dict[str, list[ClassifiedQuestion]] = {}
        self.excel_results: dict[str, list[StudentResult]] = {}
        self.analyses: dict[str, AnalysisResponse] = {}

    def new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def save_upload(self, file_id: str, filename: str, content: bytes) -> Path:
        safe_name = Path(filename).name
        folder = self.upload_dir / file_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / safe_name
        path.write_bytes(content)
        return path

    def save_questions(self, pdf_id: str, questions: list[ClassifiedQuestion]) -> None:
        self.pdf_questions[pdf_id] = questions
        self._write_json(pdf_id, "questions.json", [q.model_dump() for q in questions])

    def save_results(self, excel_id: str, results: list[StudentResult]) -> None:
        self.excel_results[excel_id] = results
        self._write_json(excel_id, "results.json", [r.model_dump() for r in results])

    def save_analysis(self, analysis: AnalysisResponse) -> None:
        self.analyses[analysis.analysis_id] = analysis
        self._write_json(
            analysis.analysis_id,
            "analysis.json",
            analysis.model_dump(mode="json"),
        )

    def _write_json(self, object_id: str, filename: str, payload: Any) -> None:
        folder = self.upload_dir / object_id
        folder.mkdir(parents=True, exist_ok=True)
        data = {
            "created_at": datetime.utcnow().isoformat(),
            "payload": payload,
        }
        (folder / filename).write_text(json.dumps(data, indent=2), encoding="utf-8")


store = AnalyticsStore()
