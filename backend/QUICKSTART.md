# Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- (Optional) Python 3.11+ for local development

## Running the Backend

### Option 1: Docker Compose (Recommended)

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Start all services:**
   ```bash
   docker-compose up --build
   ```

   This will start:
   - PostgreSQL database (port 5432)
   - Redis (port 6379)
   - FastAPI API server (port 8000)
   - Celery worker

3. **Initialize database (in another terminal):**
   ```bash
   docker-compose exec api python init_db.py
   ```

4. **Seed database (optional):**
   ```bash
   docker-compose exec api python seed.py
   ```

5. **Access the API:**
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Option 2: Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start PostgreSQL and Redis with Docker:**
   ```bash
   docker-compose up db redis
   ```

3. **Set environment variables:**
   ```bash
   export DATABASE_URL="postgresql://recruitment:recruitment123@localhost:5432/recruitment_db"
   export REDIS_URL="redis://localhost:6379/0"
   export CELERY_BROKER_URL="redis://localhost:6379/0"
   export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
   ```

4. **Initialize database:**
   ```bash
   python init_db.py
   ```

5. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start API server:**
   ```bash
   uvicorn main:app --reload
   ```

7. **Start Celery worker (in another terminal):**
   ```bash
   celery -A celery_app worker --loglevel=info
   ```

## Testing the API

### 1. Create a Job

```bash
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "We are looking for an experienced Python developer with FastAPI and PostgreSQL experience.",
    "company": "Tech Corp",
    "location": "San Francisco, CA",
    "skills": ["python", "fastapi", "postgresql", "docker", "aws"],
    "employment_type": "full-time"
  }'
```

### 2. Create a Candidate

```bash
curl -X POST "http://localhost:8000/candidates" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-0101"
  }'
```

### 3. Upload a Resume

```bash
curl -X POST "http://localhost:8000/candidates/1/resumes" \
  -F "file=@path/to/resume.pdf"
```

The resume will be automatically parsed in the background by Celery.

### 4. Get Shortlist for a Job

```bash
curl "http://localhost:8000/jobs/1/shortlist?min_score=0.5&limit=10"
```

### 5. Contact a Candidate

```bash
curl -X POST "http://localhost:8000/jobs/1/actions/contact" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": 1,
    "message": "We would like to schedule an interview"
  }'
```

### 6. Submit Feedback

```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "candidate_id": 1,
    "feedback_type": "positive",
    "rating": 5,
    "comment": "Great candidate!"
  }'
```

### 7. View Audit Logs

```bash
curl "http://localhost:8000/audit-logs?limit=10"
```

## Architecture

```
┌─────────────┐
│   FastAPI   │
│   (Port     │
│    8000)    │
└──────┬──────┘
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌─────────────┐  ┌─────────────┐
│ PostgreSQL  │  │   Redis     │
│  (Port      │  │  (Port      │
│   5432)     │  │   6379)     │
└─────────────┘  └──────┬───────┘
                       │
                       ▼
                ┌─────────────┐
                │   Celery    │
                │   Worker    │
                └─────────────┘
```

## Key Features

✅ **Job Management**: Create and parse job descriptions  
✅ **Candidate Management**: Upload resumes and extract data  
✅ **Automated Scoring**: AI-powered candidate-job matching  
✅ **Background Processing**: Async parsing with Celery  
✅ **Audit Logging**: Complete audit trail of all actions  
✅ **Mock Integrations**: Gmail and Google Calendar adapters  

## File Structure

```
backend/
├── main.py              # FastAPI app and endpoints
├── database.py          # SQLAlchemy models
├── celery_app.py        # Celery configuration
├── tasks.py             # Background tasks
├── parsers.py           # File parsing (PDF/DOCX)
├── scoring.py           # Scoring algorithm
├── adapters.py          # Mock Gmail/Calendar
├── audit.py             # Audit logging
├── config.py            # Configuration
├── seed.py              # Database seeding
├── init_db.py           # Database initialization
├── requirements.txt     # Dependencies
├── Dockerfile           # Docker image
├── docker-compose.yml   # Docker Compose config
└── alembic/             # Database migrations
```

## Troubleshooting

### Database connection issues
- Ensure PostgreSQL is running: `docker-compose ps`
- Check DATABASE_URL environment variable
- Verify database credentials in docker-compose.yml

### Celery tasks not running
- Check Redis is running: `docker-compose ps redis`
- Verify Celery worker logs: `docker-compose logs celery-worker`
- Ensure tasks are imported in celery_app.py

### File upload issues
- Check uploads directory exists and is writable
- Verify file size is under 10MB
- Check file extension is .pdf, .docx, or .doc

## Next Steps

1. Replace mock adapters with real Gmail/Google Calendar APIs
2. Enhance parsing with NLP libraries (spaCy, NLTK)
3. Add authentication and authorization
4. Implement rate limiting
5. Add comprehensive tests
6. Set up CI/CD pipeline

