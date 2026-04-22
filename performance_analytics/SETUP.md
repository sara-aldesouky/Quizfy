# Performance Analytics Service - Setup & Running Guide

## ⚡ Quick Start

### 1. Install Dependencies
```bash
cd performance_analytics
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy example to actual .env
cp ../.env.example.analytics ../.env.analytics

# Edit with your OpenAI API key
nano ../.env.analytics
```

Make sure to set:
```
OPENAI_API_KEY=sk-your-actual-key-here
ENV=production
```

### 3. Run the Service
```bash
# Option A: Direct Python
python -m performance_analytics.main

# Option B: With Uvicorn directly
uvicorn performance_analytics.api:app --host 0.0.0.0 --port 8001 --reload

# Option C: From Quizfy root
cd ../
python -m performance_analytics.main
```

The server will start on: `http://localhost:8001`

### 4. Verify Service is Running
```bash
curl http://localhost:8001/health
# Expected: {"status": "ok", "service": "performance_analytics"}
```

## 📋 Required Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | None | Your OpenAI API key |
| `OPENAI_MODEL` | No | gpt-4 | GPT model to use (gpt-4-turbo, gpt-3.5-turbo) |
| `ENV` | No | development | Environment (development, production) |
| `VECTOR_DB_TYPE` | No | chroma | Vector DB type (only chroma supported) |
| `VECTOR_DB_PATH` | No | ./chroma_db | Path to store vector DB |
| `MAX_FILE_SIZE_MB` | No | 50 | Max upload file size |
| `UPLOAD_DIR` | No | ./uploads | Directory for uploaded files |
| `LOG_LEVEL` | No | INFO | Logging level |

## 🚀 Integration with Django Quizfy

### Option A: Run as Separate Service
```bash
# Terminal 1: Django
cd /Users/sara/Desktop/Quizfy
python manage.py runserver 8000

# Terminal 2: Performance Analytics
cd /Users/sara/Desktop/Quizfy
python -m performance_analytics.main
```

Then from Django, call the performance analytics API via HTTP:
```python
import httpx

async def analyze_quiz():
    async with httpx.AsyncClient() as client:
        # Upload PDF
        with open("exam.pdf", "rb") as f:
            resp = await client.post(
                "http://localhost:8001/upload/pdf",
                files={"file": f},
                data={"exam_name": "Midterm"}
            )
        pdf_id = resp.json()["file_id"]
        
        # Upload Excel
        with open("results.xlsx", "rb") as f:
            resp = await client.post(
                "http://localhost:8001/upload/excel",
                files={"file": f},
                data={"class_name": "Math 101"}
            )
        excel_id = resp.json()["file_id"]
        
        # Run analysis
        resp = await client.post(
            "http://localhost:8001/analyze/class",
            json={
                "pdf_id": pdf_id,
                "excel_id": excel_id,
                "min_students_affected": 2
            }
        )
        analysis = resp.json()
        return analysis
```

### Option B: Integrate Directly into Django
```bash
# Copy services to Django app
cp -r performance_analytics/services quizzes/services/analytics

# Use services directly in Django views
from quizzes.services.analytics.analyzer import PerformanceAnalyzer
```

## 🧪 Testing

### Manual Testing with cURL

**Test 1: Upload PDF**
```bash
curl -X POST http://localhost:8001/upload/pdf \
  -F "file=@exam.pdf" \
  -F "exam_name=Midterm 2026" \
  -F "subject=Mathematics"
```
Response:
```json
{
  "file_id": "pdf_abc123",
  "filename": "exam.pdf",
  "records_processed": 25,
  "status": "success"
}
```

**Test 2: Upload Excel**
```bash
curl -X POST http://localhost:8001/upload/excel \
  -F "file=@results.xlsx" \
  -F "class_name=Math 101 - Section A"
```

**Test 3: Run Analysis**
```bash
curl -X POST http://localhost:8001/analyze/class \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_id": "pdf_abc123",
    "excel_id": "excel_def456",
    "min_students_affected": 2,
    "confidence_threshold": 0.70
  }'
```

### Unit Tests
```bash
pytest performance_analytics/tests/ -v
pytest performance_analytics/tests/test_scoring.py::test_class_weakness_score -v
```

## 🔍 Troubleshooting

### Error: "Missing required environment variables: OPENAI_API_KEY"
**Solution**: Set your API key
```bash
export OPENAI_API_KEY=sk-your-key-here
# Or add to .env file
```

### Error: Safari "could not send the upload request"
**Solution**: This is typically a CORS issue. Make sure:
1. Service is running on localhost:8001
2. CORS middleware is enabled (it is by default)
3. Check browser console for specific error
4. Try from different browser or with curl first

### Error: "Connection refused"
**Solution**: Service isn't running
```bash
# Check if process is listening
lsof -i :8001

# If not, start the service
python -m performance_analytics.main
```

### Error: "OpenAI API Error: Rate limit exceeded"
**Solution**: Wait a moment and retry, or:
1. Check your API quota at https://platform.openai.com
2. Reduce LLM_BATCH_SIZE in .env

### Error: PDF extraction failing
**Solution**: Ensure PDF is valid
```bash
# Test PDF is readable
python -c "import PyPDF2; PyPDF2.PdfReader('test.pdf')"
```

## 📊 Service Health Checks

```bash
# Health endpoint
curl http://localhost:8001/health

# View logs
tail -f logs/performance_analytics.log

# Monitor API requests
# Logs show all requests with status codes
```

## 🔄 Process Management

```bash
# Kill service
pkill -f "python -m performance_analytics.main"

# Check if running
ps aux | grep performance_analytics

# View port usage
sudo lsof -i :8001
```

## 📁 Directory Structure

```
performance_analytics/
├── __init__.py
├── api.py                    # FastAPI application
├── config.py                 # Configuration management
├── models.py                 # Pydantic data models
├── main.py                   # Entry point
├── requirements.txt          # Dependencies
├── prompts.py               # LLM prompts
├── security.py              # Security utilities
├── storage.py               # File storage
├── services/
│   ├── analyzer.py          # Main analysis engine
│   ├── pdf_processor.py     # PDF extraction
│   ├── excel_processor.py   # Excel normalization
│   ├── topic_classifier.py  # LLM topic classification
│   └── vector_store.py      # Vector DB (RAG)
├── tests/
│   ├── test_pdf_processor.py
│   ├── test_excel_processor.py
│   ├── test_scoring.py
│   └── test_integration.py
└── README.md
```

## 🚨 Production Deployment

### Using Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY performance_analytics/requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV ENV=production

CMD ["python", "-m", "performance_analytics.main"]
```

### Using Render/Gunicorn
```bash
# requirements.txt also includes gunicorn
gunicorn performance_analytics.api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001
```

## 📞 Support

- Check logs: `tail -f logs/performance_analytics.log`
- Test endpoint: `curl http://localhost:8001/health`
- Review API docs: `http://localhost:8001/docs`
