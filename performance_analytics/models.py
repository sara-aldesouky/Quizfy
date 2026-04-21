"""
Pydantic data models for type safety and validation.
All models include documentation, field validation, and examples.
"""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ============================================================================
# QUESTION & PDF MODELS
# ============================================================================

class QuestionChoice(BaseModel):
    """Single multiple choice option."""
    letter: str = Field(..., description="A, B, C, or D")
    text: str = Field(..., description="The choice text")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {"letter": "A", "text": "The answer is..."}
    })


class ExtractedQuestion(BaseModel):
    """A question extracted from PDF."""
    question_id: str = Field(..., description="Unique ID for this question")
    question_number: int = Field(..., description="Question number in PDF")
    question_text: str = Field(..., description="Full question text")
    answer_choices: List[QuestionChoice] = Field(
        default_factory=list,
        description="Multiple choice options (if applicable)"
    )
    correct_answer: Optional[str] = Field(
        None,
        description="The correct answer (letter or text)"
    )
    page_number: int = Field(..., description="Which page in PDF")
    source_pdf_id: str = Field(..., description="Reference to source PDF")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "question_id": "q_pdf1_001",
            "question_number": 1,
            "question_text": "What is 2 + 2?",
            "answer_choices": [
                {"letter": "A", "text": "3"},
                {"letter": "B", "text": "4"},
            ],
            "correct_answer": "B",
            "page_number": 1,
            "source_pdf_id": "pdf_abc123"
        }
    })


class ClassifiedQuestion(BaseModel):
    """Question with topic classification."""
    question_id: str
    question_number: int
    question_text: str
    answer_choices: List[QuestionChoice]
    correct_answer: Optional[str]
    page_number: int
    source_pdf_id: str
    
    # Topic classification (from LLM)
    topic: str = Field(..., description="Primary topic (e.g., 'Algebra')")
    subtopic: str = Field(..., description="Subtopic (e.g., 'Linear Equations')")
    topic_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in topic classification [0, 1]"
    )
    difficulty: Optional[Literal["easy", "medium", "hard"]] = Field(
        None,
        description="Inferred difficulty level"
    )
    skills: List[str] = Field(
        default_factory=list,
        description="Associated skill tags"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "question_id": "q_pdf1_001",
            "question_number": 1,
            "question_text": "Solve: 2x + 3 = 7",
            "answer_choices": [
                {"letter": "A", "text": "x = 1"},
                {"letter": "B", "text": "x = 2"},
            ],
            "correct_answer": "B",
            "page_number": 1,
            "source_pdf_id": "pdf_abc123",
            "topic": "Algebra",
            "subtopic": "Linear Equations",
            "topic_confidence": 0.94,
            "difficulty": "easy",
            "skills": ["equation_solving", "variable_isolation"]
        }
    })


# ============================================================================
# RESULT & EXCEL MODELS
# ============================================================================

class StudentResult(BaseModel):
    """One student's result on one question."""
    student_id: str = Field(..., description="Unique student identifier")
    student_name: Optional[str] = Field(None, description="Student name if available")
    question_number: Optional[int] = Field(None, description="Question number")
    question_id: Optional[str] = Field(None, description="Question ID")
    correct: bool = Field(..., description="Whether answer was correct")
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Partial credit if any")
    student_answer: Optional[str] = Field(None, description="What student answered")
    expected_answer: Optional[str] = Field(None, description="Expected/correct answer")
    class_name: Optional[str] = Field(None, description="Class section if available")
    exam_name: Optional[str] = Field(None, description="Exam name if available")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "student_id": "S001",
            "student_name": "Alice Johnson",
            "question_number": 5,
            "question_id": "q_pdf1_005",
            "correct": True,
            "score": 1.0,
            "student_answer": "B",
            "expected_answer": "B",
            "class_name": "Math 101 - Section A",
            "exam_name": "Midterm 2026"
        }
    })


class NormalizedResult(BaseModel):
    """Normalized result after Excel processing."""
    student_id: str
    student_name: Optional[str]
    question_number: int
    correct: bool
    score: float = Field(default=1.0, ge=0.0, le=1.0)


# ============================================================================
# WEAKNESS ANALYSIS MODELS
# ============================================================================

class WeakTopicEvidence(BaseModel):
    """Evidence supporting a weak topic finding."""
    question_number: int
    question_text: str
    correct_count: int = Field(description="How many students got this right")
    incorrect_count: int = Field(description="How many students got this wrong")
    error_rate: float = Field(description="% who got it wrong")


class StudentWeakTopic(BaseModel):
    """A weak topic for a single student."""
    topic: str
    subtopic: str
    mistake_count: int = Field(description="Mistakes on this subtopic")
    attempted_count: int = Field(description="Total attempts")
    student_error_rate: float = Field(ge=0.0, le=1.0)
    weakness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Normalized weakness score [0, 1]"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in this finding"
    )
    evidence_question_numbers: List[int]
    evidence: List[WeakTopicEvidence]
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "topic": "Algebra",
            "subtopic": "Linear Equations",
            "mistake_count": 3,
            "attempted_count": 5,
            "student_error_rate": 0.60,
            "weakness_score": 0.75,
            "confidence": 0.88,
            "evidence_question_numbers": [2, 5, 9],
            "evidence": []
        }
    })


class StudentSummary(BaseModel):
    """Complete analysis for one student."""
    student_id: str
    student_name: Optional[str]
    total_questions_attempted: int
    total_correct: int
    overall_accuracy: float = Field(ge=0.0, le=1.0)
    overall_weakness_score: float = Field(ge=0.0, le=1.0)
    weak_topics: List[StudentWeakTopic] = Field(
        description="Ranked by weakness score (descending)"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "student_id": "S001",
            "student_name": "Alice Johnson",
            "total_questions_attempted": 20,
            "total_correct": 16,
            "overall_accuracy": 0.80,
            "overall_weakness_score": 0.35,
            "weak_topics": []
        }
    })


class ClassWeakTopic(BaseModel):
    """A weak topic for the entire class."""
    topic: str
    subtopic: str
    students_affected: int = Field(description="Number of students who struggled")
    total_mistakes: int = Field(description="Total mistakes across affected students")
    total_attempts: int = Field(description="Total attempts on this topic")
    class_error_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Mistakes divided by attempts for this topic"
    )
    weakness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall weakness score for class"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in this weakness finding"
    )
    evidence_question_numbers: List[int] = Field(
        description="Question numbers supporting this finding"
    )
    evidence: List[WeakTopicEvidence]
    explanation: str = Field(
        description="Natural language explanation of why this topic is weak"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "topic": "Algebra",
            "subtopic": "Linear Equations",
            "students_affected": 12,
            "total_mistakes": 18,
            "total_attempts": 30,
            "class_error_rate": 0.60,
            "weakness_score": 0.78,
            "confidence": 0.91,
            "evidence_question_numbers": [2, 5, 9, 14],
            "evidence": [],
            "explanation": "Linear equations are a weakness across the class..."
        }
    })


class ClassSummary(BaseModel):
    """High-level class performance overview."""
    total_students: int
    total_questions: int
    class_average_accuracy: float = Field(ge=0.0, le=1.0)
    overall_class_weakness_score: float = Field(ge=0.0, le=1.0)
    weak_topics: List[ClassWeakTopic] = Field(
        description="Ranked by weakness score (descending)"
    )
    strong_topics: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Topics where class performed well"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_students": 30,
            "total_questions": 25,
            "class_average_accuracy": 0.72,
            "overall_class_weakness_score": 0.45,
            "weak_topics": [],
            "strong_topics": []
        }
    })


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request to analyze class performance."""
    pdf_id: str = Field(..., description="ID of uploaded PDF with questions")
    excel_id: str = Field(..., description="ID of uploaded Excel with results")
    min_students_affected: int = Field(
        default=2,
        ge=1,
        description="Minimum students needed for weak topic"
    )
    confidence_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for a finding [0, 1]"
    )
    filter_students: Optional[List[str]] = Field(
        None,
        description="Only analyze these student IDs (subgroup analysis)"
    )
    filter_class: Optional[str] = Field(
        None,
        description="Only analyze this class section"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "pdf_id": "pdf_abc123",
            "excel_id": "excel_def456",
            "min_students_affected": 3,
            "confidence_threshold": 0.70
        }
    })


class AnalysisResponse(BaseModel):
    """Complete analysis response."""
    analysis_id: str
    created_at: datetime
    class_summary: ClassSummary
    student_summaries: List[StudentSummary]
    metadata: Dict = Field(
        description="Processing metadata (time, questions processed, etc.)"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "analysis_id": "analysis_xyz789",
            "created_at": "2026-04-21T10:30:00Z",
            "class_summary": {},
            "student_summaries": [],
            "metadata": {
                "pdf_questions": 25,
                "excel_results": 520,
                "processing_time_ms": 2340
            }
        }
    })


class UploadResponse(BaseModel):
    """Response after file upload."""
    file_id: str = Field(description="Unique ID for uploaded file")
    filename: str
    records_processed: int
    status: Literal["success", "error"]
    message: str = Field(default="")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "file_id": "pdf_abc123",
            "filename": "midterm_2026.pdf",
            "records_processed": 25,
            "status": "success",
            "message": "25 questions extracted"
        }
    })


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    error_code: str
    details: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
