"""Class-first weakness scoring and explanation service."""

from __future__ import annotations

import json
import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Iterable

from ..config import config
from ..models import (
    AnalysisRequest,
    AnalysisResponse,
    ClassSummary,
    ClassWeakTopic,
    ClassifiedQuestion,
    StudentResult,
    StudentSummary,
    StudentWeakTopic,
    WeakTopicEvidence,
)
from ..prompts import WEAK_TOPIC_EXPLANATION_SYSTEM_PROMPT, WEAK_TOPIC_EXPLANATION_USER_PROMPT
from .vector_store import vector_store


TopicKey = tuple[str, str]


class PerformanceAnalyzer:
    """Aggregates mistakes and ranks weak topics for a full class."""

    def __init__(self) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=config.require_openai_api_key())

    def analyze(
        self,
        request: AnalysisRequest,
        questions: list[ClassifiedQuestion],
        results: list[StudentResult],
    ) -> AnalysisResponse:
        started = time.perf_counter()
        filtered_results = self._filter_results(results, request)
        matched = self._match_results(filtered_results, questions)

        total_students = len({result.student_id for result, _ in matched})
        total_questions = len(questions)
        total_attempts = len(matched)
        total_correct = sum(1 for result, _ in matched if result.correct)
        class_accuracy = total_correct / total_attempts if total_attempts else 0.0

        class_topics = self._class_weak_topics(
            matched,
            questions,
            total_students,
            request.min_students_affected,
            request.confidence_threshold,
        )
        student_summaries = self._student_summaries(matched, class_topics)
        overall_weakness = (
            sum(topic.weakness_score for topic in class_topics) / len(class_topics)
            if class_topics
            else 0.0
        )

        analysis = AnalysisResponse(
            analysis_id=f"analysis_{uuid.uuid4().hex[:12]}",
            created_at=datetime.utcnow(),
            class_summary=ClassSummary(
                total_students=total_students,
                total_questions=total_questions,
                class_average_accuracy=round(class_accuracy, 4),
                overall_class_weakness_score=round(overall_weakness, 4),
                weak_topics=class_topics,
                strong_topics=self._strong_topics(matched),
            ),
            student_summaries=student_summaries,
            metadata={
                "pdf_id": request.pdf_id,
                "excel_id": request.excel_id,
                "pdf_questions": len(questions),
                "excel_results": len(results),
                "matched_results": len(matched),
                "unmatched_results": len(filtered_results) - len(matched),
                "students_analyzed": total_students,
                "filters": {
                    "filter_students": request.filter_students,
                    "filter_class": request.filter_class,
                },
                "scoring": {
                    "class_formula": "0.4*error_rate + 0.3*affected_ratio + 0.2*mistake_volume + 0.1*confidence",
                    "student_formula": "0.5*student_error_rate + 0.3*relative_class_gap + 0.2*attempt_coverage",
                },
                "processing_time_ms": int((time.perf_counter() - started) * 1000),
            },
        )
        return analysis

    def _filter_results(
        self,
        results: list[StudentResult],
        request: AnalysisRequest,
    ) -> list[StudentResult]:
        filtered = results
        if request.filter_students:
            allowed = set(request.filter_students)
            filtered = [result for result in filtered if result.student_id in allowed]
        if request.filter_class:
            filtered = [result for result in filtered if result.class_name == request.filter_class]
        return filtered

    def _match_results(
        self,
        results: list[StudentResult],
        questions: list[ClassifiedQuestion],
    ) -> list[tuple[StudentResult, ClassifiedQuestion]]:
        by_id = {question.question_id: question for question in questions}
        by_number = {question.question_number: question for question in questions}
        matched: list[tuple[StudentResult, ClassifiedQuestion]] = []
        for result in results:
            question = None
            if result.question_id:
                question = by_id.get(result.question_id)
            if question is None and result.question_number is not None:
                question = by_number.get(result.question_number)
            if question is not None:
                matched.append((result, question))
        return matched

    def _class_weak_topics(
        self,
        matched: list[tuple[StudentResult, ClassifiedQuestion]],
        questions: list[ClassifiedQuestion],
        total_students: int,
        min_students_affected: int,
        confidence_threshold: float,
    ) -> list[ClassWeakTopic]:
        by_topic: dict[TopicKey, list[tuple[StudentResult, ClassifiedQuestion]]] = defaultdict(list)
        topic_question_count: dict[TopicKey, int] = defaultdict(int)
        for question in questions:
            topic_question_count[(question.topic, question.subtopic)] += 1
        for result, question in matched:
            by_topic[(question.topic, question.subtopic)].append((result, question))

        weak_topics: list[ClassWeakTopic] = []
        for (topic, subtopic), records in by_topic.items():
            total_attempts = len(records)
            mistakes = [(result, question) for result, question in records if not result.correct]
            total_mistakes = len(mistakes)
            if total_attempts == 0 or total_mistakes == 0:
                continue

            affected_students = {result.student_id for result, _ in mistakes}
            students_affected = len(affected_students)
            if students_affected < min_students_affected:
                continue

            class_error_rate = total_mistakes / total_attempts
            affected_ratio = students_affected / total_students if total_students else 0.0
            possible_volume = max(1, topic_question_count[(topic, subtopic)] * max(1, total_students))
            mistake_volume = min(1.0, total_mistakes / possible_volume)
            model_confidence = sum(q.topic_confidence for _, q in records) / len(records)
            confidence = self._finding_confidence(
                model_confidence=model_confidence,
                attempts=total_attempts,
                evidence_questions=len({q.question_number for _, q in mistakes}),
            )
            if confidence < confidence_threshold:
                continue

            weakness_score = min(
                1.0,
                (class_error_rate * 0.4)
                + (affected_ratio * 0.3)
                + (mistake_volume * 0.2)
                + (confidence * 0.1),
            )
            evidence = self._question_evidence(records)
            evidence_numbers = [item.question_number for item in evidence if item.incorrect_count > 0]
            weak_topic = ClassWeakTopic(
                topic=topic,
                subtopic=subtopic,
                students_affected=students_affected,
                total_mistakes=total_mistakes,
                total_attempts=total_attempts,
                class_error_rate=round(class_error_rate, 4),
                weakness_score=round(weakness_score, 4),
                confidence=round(confidence, 4),
                evidence_question_numbers=evidence_numbers,
                evidence=evidence,
                explanation=self._explain_topic(
                    topic=topic,
                    subtopic=subtopic,
                    students_affected=students_affected,
                    total_mistakes=total_mistakes,
                    total_attempts=total_attempts,
                    class_error_rate=class_error_rate,
                    evidence=evidence,
                ),
            )
            weak_topics.append(weak_topic)

        return sorted(weak_topics, key=lambda item: item.weakness_score, reverse=True)

    def _student_summaries(
        self,
        matched: list[tuple[StudentResult, ClassifiedQuestion]],
        class_topics: list[ClassWeakTopic],
    ) -> list[StudentSummary]:
        class_rates = {
            (topic.topic, topic.subtopic): topic.class_error_rate for topic in class_topics
        }
        class_max_attempts: dict[TopicKey, int] = defaultdict(int)
        by_student: dict[str, list[tuple[StudentResult, ClassifiedQuestion]]] = defaultdict(list)
        for result, question in matched:
            by_student[result.student_id].append((result, question))

        for student_records in by_student.values():
            counts: dict[TopicKey, int] = defaultdict(int)
            for _, question in student_records:
                counts[(question.topic, question.subtopic)] += 1
            for key, count in counts.items():
                class_max_attempts[key] = max(class_max_attempts[key], count)

        summaries: list[StudentSummary] = []
        for student_id, records in by_student.items():
            total_attempts = len(records)
            total_correct = sum(1 for result, _ in records if result.correct)
            by_topic: dict[TopicKey, list[tuple[StudentResult, ClassifiedQuestion]]] = defaultdict(list)
            for result, question in records:
                by_topic[(question.topic, question.subtopic)].append((result, question))

            weak_topics: list[StudentWeakTopic] = []
            for (topic, subtopic), topic_records in by_topic.items():
                mistakes = [(result, question) for result, question in topic_records if not result.correct]
                if not mistakes:
                    continue
                attempted = len(topic_records)
                mistake_count = len(mistakes)
                student_error_rate = mistake_count / attempted
                class_rate = class_rates.get((topic, subtopic), 0.0)
                relative_gap = max(0.0, (student_error_rate - class_rate) / max(0.01, 1 - class_rate))
                attempt_coverage = attempted / max(1, class_max_attempts[(topic, subtopic)])
                confidence = self._finding_confidence(
                    model_confidence=sum(q.topic_confidence for _, q in topic_records) / attempted,
                    attempts=attempted,
                    evidence_questions=len({q.question_number for _, q in mistakes}),
                )
                weakness_score = min(
                    1.0,
                    (student_error_rate * 0.5)
                    + (relative_gap * 0.3)
                    + (attempt_coverage * 0.2),
                )
                evidence = self._question_evidence(topic_records)
                weak_topics.append(
                    StudentWeakTopic(
                        topic=topic,
                        subtopic=subtopic,
                        mistake_count=mistake_count,
                        attempted_count=attempted,
                        student_error_rate=round(student_error_rate, 4),
                        weakness_score=round(weakness_score, 4),
                        confidence=round(confidence, 4),
                        evidence_question_numbers=[
                            item.question_number for item in evidence if item.incorrect_count > 0
                        ],
                        evidence=evidence,
                    )
                )

            student_name = next((result.student_name for result, _ in records if result.student_name), None)
            accuracy = total_correct / total_attempts if total_attempts else 0.0
            summaries.append(
                StudentSummary(
                    student_id=student_id,
                    student_name=student_name,
                    total_questions_attempted=total_attempts,
                    total_correct=total_correct,
                    overall_accuracy=round(accuracy, 4),
                    overall_weakness_score=round(1 - accuracy, 4),
                    weak_topics=sorted(
                        weak_topics,
                        key=lambda topic: topic.weakness_score,
                        reverse=True,
                    ),
                )
            )
        return sorted(summaries, key=lambda summary: summary.overall_weakness_score, reverse=True)

    def _question_evidence(
        self,
        records: Iterable[tuple[StudentResult, ClassifiedQuestion]],
    ) -> list[WeakTopicEvidence]:
        by_question: dict[int, dict[str, object]] = {}
        for result, question in records:
            item = by_question.setdefault(
                question.question_number,
                {"text": question.question_text, "correct": 0, "incorrect": 0},
            )
            if result.correct:
                item["correct"] = int(item["correct"]) + 1
            else:
                item["incorrect"] = int(item["incorrect"]) + 1

        evidence = []
        for question_number, item in by_question.items():
            correct = int(item["correct"])
            incorrect = int(item["incorrect"])
            attempts = correct + incorrect
            evidence.append(
                WeakTopicEvidence(
                    question_number=question_number,
                    question_text=str(item["text"]),
                    correct_count=correct,
                    incorrect_count=incorrect,
                    error_rate=round(incorrect / attempts, 4) if attempts else 0.0,
                )
            )
        return sorted(evidence, key=lambda item: (item.error_rate, item.incorrect_count), reverse=True)

    def _finding_confidence(
        self,
        model_confidence: float,
        attempts: int,
        evidence_questions: int,
    ) -> float:
        attempt_factor = min(1.0, attempts / 10)
        evidence_factor = min(1.0, evidence_questions / max(1, config.MIN_EVIDENCE_QUESTIONS))
        return max(0.0, min(1.0, (model_confidence * 0.6) + (attempt_factor * 0.25) + (evidence_factor * 0.15)))

    def _strong_topics(
        self,
        matched: list[tuple[StudentResult, ClassifiedQuestion]],
    ) -> list[dict[str, str]]:
        by_topic: dict[TopicKey, list[StudentResult]] = defaultdict(list)
        for result, question in matched:
            by_topic[(question.topic, question.subtopic)].append(result)
        strong = []
        for (topic, subtopic), results in by_topic.items():
            if len(results) < 3:
                continue
            accuracy = sum(1 for result in results if result.correct) / len(results)
            if accuracy >= 0.85:
                strong.append(
                    {
                        "topic": topic,
                        "subtopic": subtopic,
                        "accuracy": f"{accuracy:.2f}",
                    }
                )
        return strong[:10]

    def _explain_topic(
        self,
        topic: str,
        subtopic: str,
        students_affected: int,
        total_mistakes: int,
        total_attempts: int,
        class_error_rate: float,
        evidence: list[WeakTopicEvidence],
    ) -> str:
        rag_evidence = vector_store.retrieve_topic_evidence(topic, subtopic, limit=5)
        compact_evidence = [
            {
                "question_number": item.question_number,
                "question_text": item.question_text[:240],
                "incorrect_count": item.incorrect_count,
                "error_rate": item.error_rate,
            }
            for item in evidence[:5]
        ]
        if self._client:
            try:
                response = self._client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": WEAK_TOPIC_EXPLANATION_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": WEAK_TOPIC_EXPLANATION_USER_PROMPT.format(
                                topic=topic,
                                subtopic=subtopic,
                                students_affected=students_affected,
                                total_mistakes=total_mistakes,
                                total_attempts=total_attempts,
                                class_error_rate=round(class_error_rate, 4),
                                evidence_json=json.dumps(
                                    {
                                        "performance_evidence": compact_evidence,
                                        "retrieved_question_records": rag_evidence,
                                    },
                                    ensure_ascii=False,
                                ),
                            ),
                        },
                    ],
                )
                explanation = (response.choices[0].message.content or "").strip()
                if explanation:
                    return explanation
            except Exception:
                pass
        return (
            f"{subtopic} in {topic} appears weak because {students_affected} students "
            f"made {total_mistakes} mistakes across {total_attempts} attempts "
            f"({class_error_rate:.0%} error rate), especially on questions "
            f"{', '.join(str(item.question_number) for item in evidence[:4])}."
        )
