"""LLM-backed topic classification for extracted questions."""

from __future__ import annotations

import json
import re
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
            try:
                labels = self._classify_with_llm(batch, subject=subject)
            except Exception:
                labels = self._fallback_labels(batch)
            for question in batch:
                label = labels.get(question.question_id) or self._fallback_label(question)
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
        request_kwargs = {
            "model": config.OPENAI_MODEL,
            "temperature": config.OPENAI_TEMPERATURE,
            "messages": [
                {"role": "system", "content": TOPIC_CLASSIFICATION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": TOPIC_CLASSIFICATION_USER_PROMPT.format(
                        subject=subject or "Unknown",
                        questions_json=json.dumps(payload, ensure_ascii=False),
                    ),
                },
            ],
        }
        response = self._create_completion_with_json_fallback(request_kwargs)
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(self._extract_json_payload(content))
        items = parsed.get("items", [])
        return {item["question_id"]: self._normalize_label(item) for item in items}

    def _create_completion_with_json_fallback(self, request_kwargs: dict[str, Any]) -> Any:
        try:
            return self._client.chat.completions.create(
                response_format={"type": "json_object"},
                **request_kwargs,
            )
        except Exception as exc:
            if not self._is_unsupported_json_response_format_error(exc):
                raise
            return self._client.chat.completions.create(**request_kwargs)

    def _extract_json_payload(self, content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            return stripped
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
        if fenced:
            return fenced.group(1)
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return stripped[start : end + 1]
        return stripped

    def _is_unsupported_json_response_format_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return "response_format" in message and "json_object" in message and "not supported" in message

    def _fallback_labels(
        self,
        questions: list[ExtractedQuestion],
    ) -> dict[str, dict[str, Any]]:
        return {
            question.question_id: self._fallback_label(question)
            for question in questions
        }

    def _fallback_label(self, question: ExtractedQuestion) -> dict[str, Any]:
        text = question.question_text.lower()
        rules = [
            (
                r"\b(equation|solve for|linear|variable|expression|simplify|factor|algebra)\b",
                "Algebra",
                "Equations and Expressions",
                ["equation_solving", "algebraic_reasoning"],
            ),
            (
                r"\b(fraction|numerator|denominator|mixed number|equivalent fraction)\b",
                "Fractions",
                "Fraction Operations",
                ["fraction_reasoning", "number_operations"],
            ),
            (
                r"\b(decimal|percent|percentage|place value)\b",
                "Number Sense",
                "Decimals and Percents",
                ["decimal_reasoning", "percent_calculation"],
            ),
            (
                r"\b(angle|triangle|circle|area|perimeter|volume|geometry|shape)\b",
                "Geometry",
                "Shapes and Measurement",
                ["spatial_reasoning", "measurement"],
            ),
            (
                r"\b(graph|coordinate|slope|axis|plot|line graph|bar graph)\b",
                "Data and Graphs",
                "Graph Interpretation",
                ["graph_reading", "data_interpretation"],
            ),
            (
                r"\b(probability|chance|likely|unlikely|outcome)\b",
                "Probability",
                "Chance and Outcomes",
                ["probability_reasoning"],
            ),
            (
                r"\b(mean|median|mode|range|data|table|chart)\b",
                "Statistics",
                "Data Analysis",
                ["statistical_reasoning"],
            ),
            (
                r"\b(ratio|proportion|rate|unit rate)\b",
                "Ratios and Proportions",
                "Rates and Proportional Reasoning",
                ["ratio_reasoning", "proportional_thinking"],
            ),
        ]
        for pattern, topic, subtopic, skills in rules:
            if re.search(pattern, text):
                return {
                    "topic": topic,
                    "subtopic": subtopic,
                    "skills": skills,
                    "difficulty": "medium",
                    "confidence": 0.68,
                }
        return {
            "topic": "General",
            "subtopic": "Mixed Skills",
            "skills": ["general_reasoning"],
            "difficulty": "medium",
            "confidence": 0.55,
        }

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
