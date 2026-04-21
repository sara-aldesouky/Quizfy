"""Vector evidence store for question records."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Any

from ..config import config
from ..models import ClassifiedQuestion


class QuestionVectorStore:
    """Stores extracted questions for RAG-style evidence retrieval."""

    def __init__(self) -> None:
        self._local_records: list[dict[str, Any]] = []
        self._chroma_collection = None
        self._openai_client = None

    def configure(self) -> None:
        """Initialize vector dependencies during application startup."""
        self._setup_chroma()

    def ingest_questions(self, questions: list[ClassifiedQuestion]) -> None:
        if not questions:
            return
        documents = [self._document_text(question) for question in questions]
        metadatas = [self._metadata(question) for question in questions]
        ids = [question.question_id for question in questions]

        self._ensure_configured()

        embeddings = self._embed(documents)
        self._chroma_collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        for question, document, metadata in zip(questions, documents, metadatas):
            self._local_records.append(
                {
                    "id": question.question_id,
                    "document": document,
                    "metadata": metadata,
                    "tokens": Counter(self._tokens(document)),
                }
            )

    def retrieve_topic_evidence(
        self,
        topic: str,
        subtopic: str,
        source_pdf_id: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        query = f"{topic} {subtopic}"
        where = {"topic": topic, "subtopic": subtopic}
        if source_pdf_id:
            where["source_pdf"] = source_pdf_id

        self._ensure_configured()

        result = self._chroma_collection.query(
            query_embeddings=self._embed([query]),
            n_results=limit,
            where=where,
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        return [
            {"document": document, "metadata": metadata}
            for document, metadata in zip(documents, metadatas)
        ]

    def _setup_chroma(self) -> None:
        if config.VECTOR_DB_TYPE != "chroma":
            raise RuntimeError("Only Chroma vector RAG is currently implemented.")
        try:
            import chromadb
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Chroma and OpenAI dependencies are required for vector RAG."
            ) from exc

        client = chromadb.PersistentClient(path=config.VECTOR_DB_PATH)
        self._chroma_collection = client.get_or_create_collection(
            name="quizfy_questions",
            metadata={"hnsw:space": "cosine"},
        )
        self._openai_client = OpenAI(api_key=config.require_openai_api_key())

    def _ensure_configured(self) -> None:
        if not self._chroma_collection or not self._openai_client:
            raise RuntimeError("Vector RAG is not configured.")

    def _embed(self, texts: list[str]) -> list[list[float]]:
        response = self._openai_client.embeddings.create(
            model=config.EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def _document_text(self, question: ClassifiedQuestion) -> str:
        choices = " ".join(
            f"{choice.letter}. {choice.text}" for choice in question.answer_choices
        )
        return (
            f"Question {question.question_number}: {question.question_text} "
            f"{choices} Topic: {question.topic}. Subtopic: {question.subtopic}. "
            f"Skills: {', '.join(question.skills)}"
        ).strip()

    def _metadata(self, question: ClassifiedQuestion) -> dict[str, Any]:
        return {
            "question_id": question.question_id,
            "question_number": question.question_number,
            "topic": question.topic,
            "subtopic": question.subtopic,
            "source_pdf": question.source_pdf_id,
            "page_number": question.page_number,
        }

    def _tokens(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if tokens:
            return tokens
        return [hashlib.sha1(text.encode()).hexdigest()]

    def _cosine(self, left: Counter, right: Counter) -> float:
        if not left or not right:
            return 0.0
        dot = sum(left[token] * right[token] for token in left.keys() & right.keys())
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


vector_store = QuestionVectorStore()
