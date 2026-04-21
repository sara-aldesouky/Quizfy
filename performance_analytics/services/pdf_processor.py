"""PDF question extraction service."""

from __future__ import annotations

import re
from pathlib import Path

from ..models import ExtractedQuestion, QuestionChoice


QUESTION_START_RE = re.compile(
    r"(?im)^\s*(?:Q(?:uestion)?\.?\s*)?(?P<number>\d{1,3})(?:[\).\:\-]\s+|\s*$)(?P<body>.*)"
)
CHOICE_RE = re.compile(r"(?m)^\s*(?P<letter>[A-Ha-h])[\).\:\-]\s+(?P<text>.+)")
ANSWER_RE = re.compile(
    r"(?im)^\s*(?:answer|correct\s+answer|key)\s*[:\-]\s*(?P<answer>[A-H]|\S.+)$"
)


class PDFProcessor:
    """Extracts structured question records from a PDF file."""

    def extract_questions(self, pdf_path: str | Path, pdf_id: str) -> list[ExtractedQuestion]:
        pages = self._extract_pages(Path(pdf_path))
        questions: list[ExtractedQuestion] = []

        for page_number, text in pages:
            for number, block in self._split_question_blocks(text):
                choices = [
                    QuestionChoice(
                        letter=match.group("letter").upper(),
                        text=self._clean_text(match.group("text")),
                    )
                    for match in CHOICE_RE.finditer(block)
                ]
                correct_match = ANSWER_RE.search(block)
                correct_answer = (
                    self._clean_text(correct_match.group("answer")) if correct_match else None
                )
                question_text = self._clean_question_text(block)
                if not question_text:
                    continue
                questions.append(
                    ExtractedQuestion(
                        question_id=f"{pdf_id}_q{number:03d}",
                        question_number=number,
                        question_text=question_text,
                        answer_choices=choices,
                        correct_answer=correct_answer,
                        page_number=page_number,
                        source_pdf_id=pdf_id,
                    )
                )

        if questions:
            return self._dedupe_questions(questions)

        return self._fallback_unnumbered_questions(pages, pdf_id)

    def _extract_pages(self, pdf_path: Path) -> list[tuple[int, str]]:
        try:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                return [
                    (index + 1, page.extract_text() or "")
                    for index, page in enumerate(pdf.pages)
                ]
        except Exception:
            try:
                from PyPDF2 import PdfReader

                reader = PdfReader(str(pdf_path))
                return [
                    (index + 1, page.extract_text() or "")
                    for index, page in enumerate(reader.pages)
                ]
            except Exception as exc:
                raise ValueError(f"Could not read PDF content: {exc}") from exc

    def _split_question_blocks(self, text: str) -> list[tuple[int, str]]:
        matches = list(QUESTION_START_RE.finditer(text))
        blocks: list[tuple[int, str]] = []
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            number = int(match.group("number"))
            block = text[start:end].strip()
            blocks.append((number, block))
        return blocks

    def _fallback_unnumbered_questions(
        self,
        pages: list[tuple[int, str]],
        pdf_id: str,
    ) -> list[ExtractedQuestion]:
        questions: list[ExtractedQuestion] = []
        number = 1
        for page_number, text in pages:
            chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n+", text) if chunk.strip()]
            for chunk in chunks:
                if len(chunk.split()) < 6:
                    continue
                questions.append(
                    ExtractedQuestion(
                        question_id=f"{pdf_id}_q{number:03d}",
                        question_number=number,
                        question_text=self._clean_question_text(chunk),
                        answer_choices=[
                            QuestionChoice(
                                letter=match.group("letter").upper(),
                                text=self._clean_text(match.group("text")),
                            )
                            for match in CHOICE_RE.finditer(chunk)
                        ],
                        correct_answer=None,
                        page_number=page_number,
                        source_pdf_id=pdf_id,
                    )
                )
                number += 1
        return questions

    def _clean_question_text(self, block: str) -> str:
        block = CHOICE_RE.sub("", block)
        block = ANSWER_RE.sub("", block)
        block = QUESTION_START_RE.sub(lambda m: m.group("body") or "", block, count=1)
        return self._clean_text(block)

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _dedupe_questions(
        self,
        questions: list[ExtractedQuestion],
    ) -> list[ExtractedQuestion]:
        seen: set[tuple[int, str]] = set()
        deduped: list[ExtractedQuestion] = []
        for question in questions:
            key = (question.question_number, question.question_text[:80].lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(question)
        return deduped
