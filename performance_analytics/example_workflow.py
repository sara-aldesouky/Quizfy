"""
Complete example workflow for using the Performance Analytics API.
Shows real request/response cycles with sample data.
"""

import json
import httpx
from pathlib import Path


async def example_workflow():
    """
    Complete workflow:
    1. Upload PDF with questions
    2. Upload Excel with student results
    3. Run analysis
    4. Retrieve results
    """
    
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        # ============================================================
        # Step 1: Health Check
        # ============================================================
        print("\n1️⃣  Health Check")
        print("-" * 60)
        
        response = await client.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        
        # ============================================================
        # Step 2: Upload PDF
        # ============================================================
        print("\n2️⃣  Upload PDF with Questions")
        print("-" * 60)
        
        with open("sample_exam.pdf", "rb") as f:
            files = {"file": f}
            data = {
                "exam_name": "Midterm 2026",
                "subject": "Mathematics"
            }
            response = await client.post(
                f"{base_url}/upload/pdf",
                files=files,
                data=data
            )
        
        print(f"Status: {response.status_code}")
        pdf_response = response.json()
        print(json.dumps(pdf_response, indent=2))
        
        pdf_id = pdf_response["file_id"]
        print(f"\n📝 PDF ID: {pdf_id}")
        print(f"   Questions Extracted: {pdf_response['records_processed']}")
        
        
        # ============================================================
        # Step 3: Upload Excel
        # ============================================================
        print("\n3️⃣  Upload Excel with Student Results")
        print("-" * 60)
        
        with open("student_results.xlsx", "rb") as f:
            files = {"file": f}
            data = {
                "class_name": "Math 101 - Section A"
            }
            response = await client.post(
                f"{base_url}/upload/excel",
                files=files,
                data=data
            )
        
        print(f"Status: {response.status_code}")
        excel_response = response.json()
        print(json.dumps(excel_response, indent=2))
        
        excel_id = excel_response["file_id"]
        print(f"\n📊 Excel ID: {excel_id}")
        print(f"   Students: {excel_response['records_processed']} results")
        
        
        # ============================================================
        # Step 4: Run Analysis
        # ============================================================
        print("\n4️⃣  Run Class Analysis")
        print("-" * 60)
        
        analysis_request = {
            "pdf_id": pdf_id,
            "excel_id": excel_id,
            "min_students_affected": 2,
            "confidence_threshold": 0.70
        }
        
        print("Request:")
        print(json.dumps(analysis_request, indent=2))
        
        response = await client.post(
            f"{base_url}/analyze/class",
            json=analysis_request
        )
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            analysis = response.json()
            analysis_id = analysis["analysis_id"]
            
            print("\n✅ Analysis Complete!")
            print(f"   Analysis ID: {analysis_id}")
            
            # Show class summary
            print("\n📊 Class Summary:")
            class_summary = analysis["class_summary"]
            print(f"   Total Students: {class_summary['total_students']}")
            print(f"   Total Questions: {class_summary['total_questions']}")
            print(f"   Class Average: {class_summary['class_average_accuracy']:.1%}")
            print(f"   Weak Topics Found: {len(class_summary['weak_topics'])}")
            
            # Show weak topics
            print("\n🔴 Class Weak Topics:")
            for i, topic in enumerate(class_summary["weak_topics"][:3], 1):
                print(f"\n   {i}. {topic['topic']} > {topic['subtopic']}")
                print(f"      Students Affected: {topic['students_affected']}")
                print(f"      Error Rate: {topic['class_error_rate']:.1%}")
                print(f"      Weakness Score: {topic['weakness_score']:.2f}")
                print(f"      Evidence: Questions {topic['evidence_question_numbers']}")
                print(f"      Explanation: {topic['explanation'][:100]}...")
            
            # Show student summaries
            print(f"\n👥 Student Summaries ({len(analysis['student_summaries'])} students)")
            for student in analysis["student_summaries"][:2]:
                print(f"\n   Student: {student.get('student_name', student['student_id'])}")
                print(f"      Accuracy: {student['overall_accuracy']:.1%}")
                print(f"      Weak Topics: {len(student['weak_topics'])}")
                
                if student["weak_topics"]:
                    weak_topic = student["weak_topics"][0]
                    print(f"      Top Weakness: {weak_topic['topic']} > {weak_topic['subtopic']}")
                    print(f"      Weakness Score: {weak_topic['weakness_score']:.2f}")
            
            # Save full analysis
            with open("analysis_result.json", "w") as f:
                json.dump(analysis, f, indent=2)
            print(f"\n💾 Full analysis saved to: analysis_result.json")
            
        else:
            print("❌ Error:", response.text)
        
        
        # ============================================================
        # Step 5: Retrieve Specific Results
        # ============================================================
        print("\n5️⃣  Retrieve Specific Results")
        print("-" * 60)
        
        # Get class summary
        response = await client.get(
            f"{base_url}/analyze/class/summary",
            params={"analysis_id": analysis_id}
        )
        print("Class Summary Retrieved:")
        print(json.dumps(response.json()[:200], indent=2), "...")
        
        # Get student summary
        if analysis["student_summaries"]:
            first_student_id = analysis["student_summaries"][0]["student_id"]
            response = await client.get(
                f"{base_url}/analyze/student/{first_student_id}",
                params={"analysis_id": analysis_id}
            )
            print(f"\nStudent {first_student_id} Summary:")
            print(json.dumps(response.json(), indent=2))


# ============================================================
# EXPECTED RESPONSES REFERENCE
# ============================================================

EXPECTED_PDF_UPLOAD_RESPONSE = {
    "file_id": "pdf_abc123def456",
    "filename": "midterm_2026.pdf",
    "records_processed": 25,
    "status": "success",
    "message": "25 questions extracted and classified for Midterm 2026."
}

EXPECTED_EXCEL_UPLOAD_RESPONSE = {
    "file_id": "excel_xyz789uvw012",
    "filename": "results.xlsx",
    "records_processed": 120,
    "status": "success",
    "message": "30 students and 120 result rows imported."
}

EXPECTED_ANALYSIS_RESPONSE = {
    "analysis_id": "analysis_h8k2j3m9p1l5",
    "created_at": "2026-04-22T10:45:30Z",
    "class_summary": {
        "total_students": 30,
        "total_questions": 25,
        "class_average_accuracy": 0.72,
        "overall_class_weakness_score": 0.45,
        "weak_topics": [
            {
                "topic": "Algebra",
                "subtopic": "Linear Equations",
                "students_affected": 18,
                "total_mistakes": 42,
                "total_attempts": 60,
                "class_error_rate": 0.70,
                "weakness_score": 0.88,
                "confidence": 0.92,
                "evidence_question_numbers": [2, 5, 9, 14],
                "evidence": [
                    {
                        "question_number": 2,
                        "question_text": "Solve for x: 2x + 3 = 11",
                        "correct_count": 8,
                        "incorrect_count": 22,
                        "error_rate": 0.73
                    }
                ],
                "explanation": "Linear equations are a weakness across the class, with 18 of 30 students (60%) making at least one mistake. The error rate of 70% on related questions suggests students struggle with variable isolation and equation manipulation. This is a foundational skill that affects subsequent algebra topics."
            },
            {
                "topic": "Fractions",
                "subtopic": "Adding Fractions",
                "students_affected": 12,
                "total_mistakes": 15,
                "total_attempts": 24,
                "class_error_rate": 0.625,
                "weakness_score": 0.72,
                "confidence": 0.88,
                "evidence_question_numbers": [7, 11],
                "evidence": [],
                "explanation": "While fewer students struggle with fractions than algebra, those who do tend to make consistent errors in finding common denominators."
            }
        ],
        "strong_topics": [
            {"topic": "Geometry", "subtopic": "Basic Shapes", "accuracy": 0.90},
            {"topic": "Basic Arithmetic", "subtopic": "Multiplication", "accuracy": 0.85}
        ]
    },
    "student_summaries": [
        {
            "student_id": "S001",
            "student_name": "Alice Johnson",
            "total_questions_attempted": 25,
            "total_correct": 22,
            "overall_accuracy": 0.88,
            "overall_weakness_score": 0.25,
            "weak_topics": [
                {
                    "topic": "Algebra",
                    "subtopic": "Quadratic Equations",
                    "mistake_count": 1,
                    "attempted_count": 3,
                    "student_error_rate": 0.33,
                    "weakness_score": 0.35,
                    "confidence": 0.85,
                    "evidence_question_numbers": [15],
                    "evidence": []
                }
            ]
        },
        {
            "student_id": "S002",
            "student_name": "Bob Smith",
            "total_questions_attempted": 25,
            "total_correct": 16,
            "overall_accuracy": 0.64,
            "overall_weakness_score": 0.62,
            "weak_topics": [
                {
                    "topic": "Algebra",
                    "subtopic": "Linear Equations",
                    "mistake_count": 4,
                    "attempted_count": 5,
                    "student_error_rate": 0.80,
                    "weakness_score": 0.85,
                    "confidence": 0.91,
                    "evidence_question_numbers": [2, 5, 9],
                    "evidence": []
                },
                {
                    "topic": "Fractions",
                    "subtopic": "Adding Fractions",
                    "mistake_count": 2,
                    "attempted_count": 3,
                    "student_error_rate": 0.67,
                    "weakness_score": 0.72,
                    "confidence": 0.88,
                    "evidence_question_numbers": [7, 11],
                    "evidence": []
                }
            ]
        }
    ],
    "metadata": {
        "pdf_questions_processed": 25,
        "excel_results_processed": 750,
        "unique_students": 30,
        "processing_time_ms": 3245,
        "vector_db_ingested": 25
    }
}

EXPECTED_ERROR_RESPONSE = {
    "error": "Failed to process PDF: Invalid PDF format",
    "error_code": "PDF_PROCESSING_ERROR",
    "details": {
        "file": "exam.pdf",
        "reason": "Could not extract text from PDF"
    },
    "timestamp": "2026-04-22T10:45:30Z"
}


if __name__ == "__main__":
    import asyncio
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║   Quizfy Performance Analytics - Example Workflow             ║
    ║   Full-Class Weakness Analysis                                ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print("Note: Make sure the service is running first:")
    print("  python -m performance_analytics.main\n")
    
    try:
        asyncio.run(example_workflow())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. Service is running (python -m performance_analytics.main)")
        print("  2. You have sample PDF and Excel files (sample_exam.pdf, student_results.xlsx)")
        print("  3. OpenAI API key is set (export OPENAI_API_KEY=sk-...)")
