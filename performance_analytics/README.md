# Performance Analytics Service

## 🎓 Overview

A production-grade backend service for analyzing class-level and student-level academic performance. Identifies weak topics across the entire classroom using:
- PDF-based question extraction
- Excel-based student results
- AI-powered topic classification
- Vector database RAG for explainability

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  FastAPI Server (port 8001)                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  API Endpoints                                          │
│  ├── POST /upload/pdf                                   │
│  ├── POST /upload/excel                                 │
│  ├── POST /analyze/class                                │
│  ├── GET /analyze/class/summary                         │
│  ├── GET /analyze/student/{student_id}                  │
│  └── GET /analyze/filter                                │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  Services Layer                                         │
│  ├── PDFProcessor → Question extraction                 │
│  ├── ExcelProcessor → Results normalization             │
│  ├── TopicClassifier → LLM-based topic inference        │
│  ├── PerformanceAnalyzer → Weakness scoring             │
│  └── RAGExplainer → Evidence retrieval                  │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  Data Layer                                             │
│  ├── Pydantic Models (type safety)                      │
│  ├── Vector DB (Chroma)                                 │
│  └── In-memory cache (results)                          │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  External Services                                      │
│  ├── OpenAI API (GPT-4, GPT-3.5)                       │
│  └── PDF parsing (PyPDF2, pdfplumber)                   │
└─────────────────────────────────────────────────────────┘
```

## 📊 Data Flow

```
1. PDF Upload
   ↓
   PDFProcessor.extract_questions()
   ├─ Extract question_text, answer_choices, correct_answer
   ├─ Preserve question_number, page_number
   └─ Store raw questions
   ↓
2. Topic Classification
   ↓
   TopicClassifier.classify_batch()
   ├─ Send to OpenAI with few-shot examples
   ├─ Receive topic, subtopic, confidence
   └─ Store classified questions
   ↓
3. Vector DB Ingestion
   ↓
   RAGExplainer.ingest_questions()
   ├─ Generate embeddings for each question
   ├─ Store metadata (topic, subtopic, question_id)
   └─ Create searchable knowledge base
   ↓
4. Excel Upload
   ↓
   ExcelProcessor.normalize_results()
   ├─ Map flexible column names to standard schema
   ├─ Match results to question IDs
   └─ Structure: {student_id, question_number, correct/incorrect}
   ↓
5. Class Analysis
   ↓
   PerformanceAnalyzer.analyze_class()
   ├─ Aggregate mistakes by topic
   ├─ Calculate class-level weakness scores
   ├─ Retrieve evidence questions from RAG
   └─ Generate explanations
   ↓
6. Output: Class Summary + Student Breakdowns
```

## 📋 Key Components

### A. PDFProcessor
- Extracts questions from PDF with flexible formatting
- Handles: numbered, unnumbered, mixed questions
- Returns: question_text, answer_choices, correct_answer, page_number

### B. ExcelProcessor
- Normalizes flexible Excel column names
- Supports: student_id, question_number, correct/incorrect, score
- Returns: standardized result records

### C. TopicClassifier
- Uses OpenAI to infer topic/subtopic from question text
- Few-shot examples for consistency
- Confidence scoring built-in

### D. PerformanceAnalyzer
- Aggregates errors by topic (class-level)
- Calculates per-student weakness scores
- Scoring formula includes:
  - Error rate
  - Number of affected students
  - Confidence threshold
  - Difficulty weighting (optional)

### E. RAGExplainer
- Stores questions in vector DB (Chroma)
- Retrieves supporting evidence questions
- Generates natural language explanations using question context

## 🔢 Scoring Formulas

### Class-Level Weakness Score
```
weakness_score = (error_rate × 0.4) + (affected_ratio × 0.3) + (mistake_volume × 0.2) + (confidence × 0.1)

Where:
- error_rate = total_mistakes / total_attempts
- affected_ratio = students_with_mistakes / total_students
- mistake_volume = total_mistakes / (topic_question_count × total_students)
- confidence = average_model_confidence
```

### Student-Level Weakness Score
```
weakness_score = (student_error_rate × 0.5) + (relative_class_performance × 0.3) + (attempt_count × 0.2)

Where:
- student_error_rate = student_mistakes / student_attempts
- relative_class_performance = (student_error_rate - class_avg_rate)
- attempt_count = (student_attempts / max_attempts_in_topic) [0,1 normalized]
```

## 📦 Required Dependencies

```
fastapi>=0.100.0
pydantic>=2.0.0
pandas>=2.0.0
numpy>=1.24.0
PyPDF2>=3.0.0
pdfplumber>=0.10.0
openai>=1.0.0
chromadb>=0.4.0
python-dotenv>=1.0.0
aiofiles>=23.0.0
uvicorn>=0.23.0
```

## 🚀 Running the Service

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure environment variables are configured securely
export OPENAI_MODEL=gpt-4o-mini
export VECTOR_DB_PATH=./chroma_db

# Run server
python -m uvicorn performance_analytics.api:app --host 0.0.0.0 --port 8001 --reload

# Server runs on http://localhost:8001
```

## 📡 API Endpoints

### Upload PDF
```
POST /upload/pdf
Body: {
  "file": <binary>,
  "exam_name": "Midterm 2026",
  "subject": "Mathematics"
}
Response: {
  "pdf_id": "pdf_abc123",
  "questions_extracted": 25,
  "status": "success"
}
```

### Upload Excel
```
POST /upload/excel
Body: {
  "file": <binary>,
  "class_name": "Math 101 - Section A"
}
Response: {
  "excel_id": "excel_def456",
  "students_found": 30,
  "results_imported": 180,
  "status": "success"
}
```

### Run Class Analysis
```
POST /analyze/class
Body: {
  "pdf_id": "pdf_abc123",
  "excel_id": "excel_def456",
  "min_students_affected": 3,
  "confidence_threshold": 0.7
}
Response: {
  "class_summary": {...},
  "student_summaries": [...],
  "metadata": {...}
}
```

## 🔒 Security

- All API keys loaded from environment variables
- No hardcoded secrets
- Input validation via Pydantic
- File size limits enforced
- LLM calls only from secure backend
- CORS configured for frontend integration

## 🧪 Testing

```bash
pytest performance_analytics/tests/ -v
pytest performance_analytics/tests/test_scoring.py::test_class_weakness_score
```

## 📚 Integration with Quizfy

The service is designed to integrate with your existing Django Quizfy platform:

1. **Option A**: Run as separate FastAPI microservice
   - Call from Quizzy via HTTP
   - Independent scaling
   - Service discovery via environment variables

2. **Option B**: Integrate directly into Django
   - Add as Django app
   - Shared database
   - Django ORM models

Both options supported through modular service design.

## 🛠️ Customization

### Add Custom Topic Categories
Edit `prompts.py` → `TOPIC_CLASSIFICATION_SYSTEM_PROMPT` and `TOPIC_CLASSIFICATION_USER_PROMPT`

## ✅ Implemented Backend Modules

This package now contains a runnable FastAPI microservice:

```
performance_analytics/
├── api.py                         # FastAPI routes and startup validation
├── config.py                      # env-based settings, no hardcoded secrets
├── models.py                      # Pydantic request/response/data contracts
├── prompts.py                     # internal LLM prompts
├── storage.py                     # upload/result/analysis persistence boundary
└── services/
    ├── analyzer.py                # class and student weakness scoring
    ├── excel_processor.py         # flexible Excel/CSV normalization
    ├── pdf_processor.py           # PDF question extraction
    ├── topic_classifier.py        # OpenAI classification
    └── vector_store.py            # Chroma/OpenAI embedding RAG
```

## 🧠 Internal LLM Prompts

Prompts live in `performance_analytics/prompts.py`:

- `TOPIC_CLASSIFICATION_SYSTEM_PROMPT`
- `TOPIC_CLASSIFICATION_USER_PROMPT`
- `WEAK_TOPIC_EXPLANATION_SYSTEM_PROMPT`
- `WEAK_TOPIC_EXPLANATION_USER_PROMPT`

The classifier requests strict JSON with `topic`, `subtopic`, `skills`, `difficulty`, and `confidence`. The explainer receives only performance evidence and retrieved question records, then returns a concise teacher-facing explanation.

## 🔌 API Design

### `POST /upload/pdf`
Multipart form:

- `file`: PDF assessment
- `exam_name`: optional
- `subject`: optional hint for topic classification

The service extracts question records, classifies them, ingests them into the vector store, and returns a `pdf_*` ID.

### `POST /upload/excel`
Multipart form:

- `file`: `.xlsx`, `.xls`, `.csv`, or `.tsv`
- `class_name`: optional default class label

The service normalizes long-format sheets and wide-format sheets such as `Q1`, `Q2`, `Q3`, then returns an `excel_*` ID.

### `POST /analyze/class`
JSON body:

```json
{
  "pdf_id": "pdf_abc123",
  "excel_id": "excel_def456",
  "min_students_affected": 3,
  "confidence_threshold": 0.7,
  "filter_students": null,
  "filter_class": null
}
```

Returns class-level weak topics and all student summaries. Filters make subgroup analysis possible without changing the class-first workflow.

### `GET /analyze/class/summary`
Returns the latest class summary, or pass `analysis_id`.

### `GET /analyze/student/{student_id}`
Returns one student summary from the latest analysis, or pass `analysis_id`.

### `GET /analyze/filter`
Convenience endpoint for rerunning an analysis by `pdf_id`, `excel_id`, optional repeated `student_id`, and optional `class_name`.

## 📐 Data Models

Important Pydantic models:

- `ExtractedQuestion`: PDF-derived question text, choices, answer key if present, page, source PDF
- `ClassifiedQuestion`: extracted question plus topic, subtopic, confidence, difficulty, skills
- `StudentResult`: normalized student/question result row
- `ClassWeakTopic`: ranked class weakness with affected students, attempts, mistakes, confidence, evidence, explanation
- `StudentWeakTopic`: ranked student weakness with mistake counts and evidence
- `AnalysisResponse`: top-level response for frontend rendering

## 🧮 Scoring

### Class-level

```
weakness_score =
  0.4 * class_error_rate +
  0.3 * affected_ratio +
  0.2 * mistake_volume +
  0.1 * confidence
```

Where:

- `class_error_rate = total_mistakes / total_attempts`
- `affected_ratio = students_with_mistakes / total_students`
- `mistake_volume = total_mistakes / (topic_question_count * total_students)`
- `confidence = 0.6 * average_topic_confidence + 0.25 * attempt_factor + 0.15 * evidence_factor`

### Student-level

```
weakness_score =
  0.5 * student_error_rate +
  0.3 * relative_class_gap +
  0.2 * attempt_coverage
```

Where:

- `student_error_rate = student_topic_mistakes / student_topic_attempts`
- `relative_class_gap = max(0, student_error_rate - class_topic_error_rate) / (1 - class_topic_error_rate)`
- `attempt_coverage = student_topic_attempts / max_topic_attempts_seen_for_any_student`

## 🧾 Example Response

```json
{
  "analysis_id": "analysis_a1b2c3d4e5f6",
  "created_at": "2026-04-21T10:30:00Z",
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
        "class_error_rate": 0.7,
        "weakness_score": 0.88,
        "confidence": 0.92,
        "evidence_question_numbers": [2, 5, 9, 14],
        "evidence": [],
        "explanation": "A large portion of the class missed questions involving solving and rearranging linear equations."
      }
    ],
    "strong_topics": []
  },
  "student_summaries": [
    {
      "student_id": "S001",
      "student_name": "Student A",
      "total_questions_attempted": 20,
      "total_correct": 16,
      "overall_accuracy": 0.8,
      "overall_weakness_score": 0.2,
      "weak_topics": [
        {
          "topic": "Algebra",
          "subtopic": "Linear Equations",
          "mistake_count": 4,
          "attempted_count": 5,
          "student_error_rate": 0.8,
          "weakness_score": 0.9,
          "confidence": 0.89,
          "evidence_question_numbers": [2, 5, 9, 14],
          "evidence": []
        }
      ]
    }
  ],
  "metadata": {
    "matched_results": 520,
    "unmatched_results": 0,
    "students_analyzed": 30
  }
}
```

## 🛡️ Edge Cases and Safeguards

- Missing `OPENAI_API_KEY` fails startup with a clear error.
- Upload size is capped by `MAX_FILE_SIZE_MB`.
- PDF parser tries `pdfplumber`, then `PyPDF2`, then falls back to paragraph-based unnumbered extraction.
- Excel parser supports long result rows and wide question columns like `Q1`, `Q2`, `Question 3`.
- Matching prefers `question_id`, then falls back to `question_number`.
- Unmatched rows are counted in response metadata.
- Confidence is lowered when evidence is thin, even if the error rate is high.
- API keys are only read from environment variables.
- LLM calls happen only in the backend service.

## 🏁 Implementation Plan

1. Run this FastAPI service as a microservice next to the existing Django app.
2. Add authentication between Django and the analytics service.
3. Replace the in-process `AnalyticsStore` with PostgreSQL models when persistence across workers is required.
4. Keep Chroma for local/simple deployments, or move vectors to pgvector if you want one database for relational data and embeddings.
5. Add teacher-facing Django pages that call these APIs and render the returned JSON.

### Adjust Weakness Scoring
Edit `scoring.py` → `WeaknessScorer.calculate_class_weakness()`

### Change Vector DB
The current implementation uses Chroma. Add a new vector-store adapter before changing `VECTOR_DB_TYPE`.

### Modify Confidence Thresholds
Edit `config.py` → Adjust `CONFIDENCE_THRESHOLD`

---

**Author**: Quizfy Performance Analytics Team  
**Version**: 1.0.0  
**Status**: Production-Ready
