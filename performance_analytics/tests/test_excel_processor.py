from openpyxl import Workbook

from performance_analytics.services.excel_processor import ExcelProcessor


def test_normalize_results_detects_quiz_export_header_rows(tmp_path):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Submissions"

    worksheet.append(["Quiz Submissions Report"])
    worksheet.append(["Quiz: Midterm | Code: ABC123"])
    worksheet.append([])
    worksheet.append(
        [
            "Student Full Name",
            "University ID",
            "Score",
            "Total",
            "Percentage",
            "Submitted At",
            "Q1",
            "Q2",
        ]
    )
    worksheet.append(["Student A", "S001", 1, 2, 0.5, "2026-04-21 10:00", 1, 0])
    worksheet.append(["Student B", "S002", 2, 2, 1.0, "2026-04-21 10:05", 1, 1])

    path = tmp_path / "quiz_export.xlsx"
    workbook.save(path)

    results = ExcelProcessor().normalize_results(path)

    assert len(results) == 4
    assert [(result.student_id, result.student_name, result.question_number, result.correct) for result in results] == [
        ("S001", "Student A", 1, True),
        ("S001", "Student A", 2, False),
        ("S002", "Student B", 1, True),
        ("S002", "Student B", 2, True),
    ]

