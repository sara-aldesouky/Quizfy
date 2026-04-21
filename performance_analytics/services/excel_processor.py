"""Excel result normalization service."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..models import StudentResult


CANONICAL_COLUMNS = {
    "student_id": {
        "student_id",
        "student id",
        "studentid",
        "id",
        "learner_id",
        "learner id",
        "roll_number",
        "roll no",
    },
    "student_name": {
        "student_name",
        "student name",
        "name",
        "learner_name",
        "learner name",
        "full_name",
    },
    "question_number": {
        "question_number",
        "question number",
        "question_no",
        "question no",
        "q_number",
        "q no",
        "number",
    },
    "question_id": {"question_id", "question id", "qid", "item_id", "item id"},
    "correct": {
        "correct_incorrect",
        "correct/incorrect",
        "correct",
        "is_correct",
        "status",
        "result",
    },
    "score": {"score", "points", "mark", "marks", "grade"},
    "expected_answer": {"expected_answer", "expected answer", "correct_answer", "answer_key"},
    "student_answer": {"student_answer", "student answer", "response", "answer"},
    "class_name": {"class_name", "class name", "section", "class", "group"},
    "exam_name": {"exam_name", "exam name", "assessment", "test", "quiz"},
}


class ExcelProcessor:
    """Normalizes flexible class-result spreadsheets into row records."""

    def normalize_results(self, excel_path: str | Path) -> list[StudentResult]:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("pandas is required to process Excel files") from exc

        suffix = Path(excel_path).suffix.lower()
        if suffix == ".csv":
            dataframe = pd.read_csv(excel_path)
        elif suffix == ".tsv":
            dataframe = pd.read_csv(excel_path, sep="\t")
        else:
            dataframe = pd.read_excel(excel_path)

        dataframe = dataframe.dropna(how="all")
        if dataframe.empty:
            return []

        column_map = self._build_column_map(dataframe.columns)
        if "question_number" in column_map or "question_id" in column_map:
            return self._normalize_long_format(dataframe, column_map)

        return self._normalize_wide_format(dataframe, column_map)

    def _normalize_long_format(self, dataframe: Any, column_map: dict[str, str]) -> list[StudentResult]:
        results: list[StudentResult] = []
        for _, row in dataframe.iterrows():
            student_id = self._string_value(row.get(column_map.get("student_id")))
            student_name = self._string_value(row.get(column_map.get("student_name")))
            if not student_id:
                student_id = student_name or f"row_{len(results) + 1}"

            question_number = self._int_value(row.get(column_map.get("question_number")))
            question_id = self._string_value(row.get(column_map.get("question_id")))
            if question_number is None and not question_id:
                continue

            score = self._score_value(row.get(column_map.get("score")))
            correct = self._correct_value(
                row.get(column_map.get("correct")),
                score=score,
                student_answer=row.get(column_map.get("student_answer")),
                expected_answer=row.get(column_map.get("expected_answer")),
            )
            results.append(
                StudentResult(
                    student_id=student_id,
                    student_name=student_name,
                    question_number=question_number,
                    question_id=question_id,
                    correct=correct,
                    score=score if score is not None else (1.0 if correct else 0.0),
                    student_answer=self._string_value(row.get(column_map.get("student_answer"))),
                    expected_answer=self._string_value(row.get(column_map.get("expected_answer"))),
                    class_name=self._string_value(row.get(column_map.get("class_name"))),
                    exam_name=self._string_value(row.get(column_map.get("exam_name"))),
                )
            )
        return results

    def _normalize_wide_format(self, dataframe: Any, column_map: dict[str, str]) -> list[StudentResult]:
        question_columns = [
            column for column in dataframe.columns if self._question_number_from_header(str(column))
        ]
        if not question_columns:
            raise ValueError(
                "Could not find question_number/question_id columns or wide question columns like Q1."
            )

        results: list[StudentResult] = []
        for row_index, row in dataframe.iterrows():
            student_id = self._string_value(row.get(column_map.get("student_id")))
            student_name = self._string_value(row.get(column_map.get("student_name")))
            if not student_id:
                student_id = student_name or f"row_{row_index + 1}"

            for column in question_columns:
                value = row.get(column)
                question_number = self._question_number_from_header(str(column))
                score = self._score_value(value)
                correct = self._correct_value(value, score=score)
                results.append(
                    StudentResult(
                        student_id=student_id,
                        student_name=student_name,
                        question_number=question_number,
                        correct=correct,
                        score=score if score is not None else (1.0 if correct else 0.0),
                        class_name=self._string_value(row.get(column_map.get("class_name"))),
                        exam_name=self._string_value(row.get(column_map.get("exam_name"))),
                    )
                )
        return results

    def _build_column_map(self, columns: list[str]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        normalized_lookup = {self._normalize_header(column): column for column in columns}
        for canonical, aliases in CANONICAL_COLUMNS.items():
            for alias in aliases:
                normalized_alias = self._normalize_header(alias)
                if normalized_alias in normalized_lookup:
                    mapping[canonical] = normalized_lookup[normalized_alias]
                    break
        return mapping

    def _normalize_header(self, value: Any) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()

    def _question_number_from_header(self, header: str) -> int | None:
        match = re.match(r"^\s*(?:q|question|item)\s*[_\-\s\.]*(\d{1,3})\s*$", header, re.I)
        return int(match.group(1)) if match else None

    def _correct_value(
        self,
        value: Any,
        score: float | None = None,
        student_answer: Any = None,
        expected_answer: Any = None,
    ) -> bool:
        text = self._string_value(value)
        if text:
            normalized = text.lower()
            if normalized in {"correct", "right", "true", "yes", "y", "1", "pass", "passed"}:
                return True
            if normalized in {"incorrect", "wrong", "false", "no", "n", "0", "fail", "failed"}:
                return False
        if student_answer is not None and expected_answer is not None:
            return self._string_value(student_answer).lower() == self._string_value(expected_answer).lower()
        if score is not None:
            return score >= 0.999
        return False

    def _score_value(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            import pandas as pd

            if pd.isna(value):
                return None
        except Exception:
            pass
        if isinstance(value, str):
            cleaned = value.strip().replace("%", "")
            if not cleaned or cleaned.lower() in {"correct", "right", "true", "yes"}:
                return 1.0 if cleaned else None
            if cleaned.lower() in {"incorrect", "wrong", "false", "no"}:
                return 0.0
            value = cleaned
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if numeric > 1:
            numeric = numeric / 100 if numeric <= 100 else 1.0
        return max(0.0, min(1.0, numeric))

    def _int_value(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            import pandas as pd

            if pd.isna(value):
                return None
        except Exception:
            pass
        match = re.search(r"\d+", str(value))
        return int(match.group(0)) if match else None

    def _string_value(self, value: Any) -> str | None:
        if value is None:
            return None
        try:
            import pandas as pd

            if pd.isna(value):
                return None
        except Exception:
            pass
        text = str(value).strip()
        return text or None

