from performance_analytics.models import ExtractedQuestion
from performance_analytics.services.topic_classifier import TopicClassifier


def test_fallback_label_identifies_algebra_question_without_client_call():
    classifier = TopicClassifier.__new__(TopicClassifier)
    question = ExtractedQuestion(
        question_id="pdf_1_q001",
        question_number=1,
        question_text="Solve the equation 2x + 3 = 11.",
        answer_choices=[],
        correct_answer=None,
        page_number=1,
        source_pdf_id="pdf_1",
    )

    label = classifier._fallback_label(question)

    assert label["topic"] == "Algebra"
    assert label["subtopic"] == "Equations and Expressions"
    assert label["confidence"] >= 0.65

