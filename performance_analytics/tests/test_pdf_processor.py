from performance_analytics.services.pdf_processor import PDFProcessor


def test_split_question_blocks_handles_quiz_export_question_headers():
    processor = PDFProcessor()
    text = """
QUESTION 1
Solve 2 + 2.
A. 3
B. 4

QUESTION 2
Which shape has three sides?
A. Square
B. Triangle
"""

    blocks = processor._split_question_blocks(text)

    assert [number for number, _ in blocks] == [1, 2]
    assert "Solve 2 + 2" in processor._clean_question_text(blocks[0][1])
    assert "Which shape" in processor._clean_question_text(blocks[1][1])

