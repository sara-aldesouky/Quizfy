from performance_analytics.models import AnalysisRequest, ClassifiedQuestion, StudentResult
from performance_analytics.services.analyzer import PerformanceAnalyzer


def _question(number, topic="Algebra", subtopic="Linear Equations"):
    return ClassifiedQuestion(
        question_id=f"pdf_1_q{number:03d}",
        question_number=number,
        question_text=f"Solve linear equation {number}",
        answer_choices=[],
        correct_answer=None,
        page_number=1,
        source_pdf_id="pdf_1",
        topic=topic,
        subtopic=subtopic,
        topic_confidence=0.95,
        difficulty="medium",
        skills=["equation_solving"],
    )


def test_class_weakness_score_ranks_topic_by_error_rate_and_affected_students():
    questions = [_question(1), _question(2), _question(3, "Geometry", "Angles")]
    results = [
        StudentResult(student_id="S1", question_number=1, correct=False),
        StudentResult(student_id="S1", question_number=2, correct=False),
        StudentResult(student_id="S1", question_number=3, correct=True),
        StudentResult(student_id="S2", question_number=1, correct=False),
        StudentResult(student_id="S2", question_number=2, correct=True),
        StudentResult(student_id="S2", question_number=3, correct=True),
        StudentResult(student_id="S3", question_number=1, correct=True),
        StudentResult(student_id="S3", question_number=2, correct=False),
        StudentResult(student_id="S3", question_number=3, correct=False),
    ]

    response = PerformanceAnalyzer().analyze(
        AnalysisRequest(
            pdf_id="pdf_1",
            excel_id="excel_1",
            min_students_affected=1,
            confidence_threshold=0.0,
        ),
        questions,
        results,
    )

    top = response.class_summary.weak_topics[0]
    assert top.topic == "Algebra"
    assert top.subtopic == "Linear Equations"
    assert top.students_affected == 3
    assert top.total_mistakes == 4
    assert top.total_attempts == 6
    assert top.evidence_question_numbers == [1, 2]


def test_student_weak_topics_include_evidence_question_numbers():
    questions = [_question(1), _question(2)]
    results = [
        StudentResult(student_id="S1", student_name="Student A", question_number=1, correct=False),
        StudentResult(student_id="S1", student_name="Student A", question_number=2, correct=True),
    ]

    response = PerformanceAnalyzer().analyze(
        AnalysisRequest(
            pdf_id="pdf_1",
            excel_id="excel_1",
            min_students_affected=1,
            confidence_threshold=0.0,
        ),
        questions,
        results,
    )

    summary = response.student_summaries[0]
    assert summary.student_id == "S1"
    assert summary.student_name == "Student A"
    assert summary.weak_topics[0].mistake_count == 1
    assert summary.weak_topics[0].evidence_question_numbers == [1]

