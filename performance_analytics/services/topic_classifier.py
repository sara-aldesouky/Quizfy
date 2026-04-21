"""LLM-backed topic classification for extracted questions."""

from __future__ import annotations

import json
from typing import Any

from ..config import config
from ..models import ClassifiedQuestion, ExtractedQuestion
from ..prompts import TOPIC_CLASSIFICATION_SYSTEM_PROMPT, TOPIC_CLASSIFICATION_USER_PROMPT


class TopicClassifier:
    """Assigns primary topic, subtopic, skills, difficulty, and confidence."""

    def __init__(self) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=config.require_openai_api_key())

    def classify_batch(
        self,
        questions: list[ExtractedQuestion],
        subject: str | None = None,
    ) -> list[ClassifiedQuestion]:
        classified: list[ClassifiedQuestion] = []
        for start in range(0, len(questions), config.LLM_BATCH_SIZE):
            batch = questions[start : start + config.LLM_BATCH_SIZE]
            labels = self._classify_with_llm(batch, subject=subject)
            for question in batch:
                label = labels.get(question.question_id)
                if label is None:
                    raise RuntimeError(
                        f"Topic classification missing for question {question.question_id}"
                    )
                classified.append(
                    ClassifiedQuestion(
                        **question.model_dump(),
                        topic=label["topic"],
                        subtopic=label["subtopic"],
                        topic_confidence=label["confidence"],
                        difficulty=label.get("difficulty"),
                        skills=label.get("skills", []),
                    )
                )
        return classified

    def _classify_with_llm(
        self,
        questions: list[ExtractedQuestion],
        subject: str | None,
    ) -> dict[str, dict[str, Any]]:
        payload = [
            {
                "question_id": q.question_id,
                "question_number": q.question_number,
                "question_text": q.question_text,
                "answer_choices": [choice.model_dump() for choice in q.answer_choices],
            }
            for q in questions
        ]
        response = self._client.chat.completions.create(
            model=config.OPENAI_MODEL,
            temperature=config.OPENAI_TEMPERATURE,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": TOPIC_CLASSIFICATION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": TOPIC_CLASSIFICATION_USER_PROMPT.format(
                        subject=subject or "Unknown",
                        questions_json=json.dumps(payload, ensure_ascii=False),
                    ),
                },
            ],
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        items = parsed.get("items", [])
        return {item["question_id"]: self._normalize_label(item) for item in items}

    def _normalize_label(self, item: dict[str, Any]) -> dict[str, Any]:
        confidence = float(item.get("confidence", item.get("topic_confidence", 0.65)))
        difficulty = item.get("difficulty") if item.get("difficulty") in {"easy", "medium", "hard"} else None
        skills = item.get("skills") if isinstance(item.get("skills"), list) else []
        return {
            "topic": str(item.get("topic") or "Uncategorized").strip() or "Uncategorized",
            "subtopic": str(item.get("subtopic") or "General").strip() or "General",
            "skills": [str(skill)[:64] for skill in skills[:5]],
            "difficulty": difficulty,
            "confidence": max(0.0, min(1.0, confidence)),
        }
