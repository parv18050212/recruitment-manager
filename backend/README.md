# Agentic AI Recruitment Manager - Backend

An autonomous AI system that handles hiring end-to-end using FastAPI, PostgreSQL, Redis, and Celery.

## Features

- **Job Management**: Upload and parse job descriptions to create structured job profiles
- **Candidate Management**: Upload candidate resumes (PDF/DOCX) and extract structured data
- **Automated Scoring**: Compare candidates vs jobs with fit_score, confidence, and reasoning
- **Background Processing**: Async parsing and scoring using Celery workers
- **Audit Logging**: Every automated action is logged with reasoning and confidence
- **Mock Integrations**: Gmail (email sending) and Google Calendar (scheduling) adapters

## Tech Stack

- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Relational database
- **Redis**: Message broker for Celery
- **Celery**: Distributed task queue for async processing
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migrations
- **PyPDF2**: PDF parsing
- **python-docx**: DOCX parsing

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Running with Docker Compose

1. **Start all services:**
   ```bash
   cd backend
   docker-compose up --build
   ```

   This will start:
   - PostgreSQL database (port 5432)
   - Redis (port 6379)
   - FastAPI API server (port 8000)
   - Celery worker

2. **Initialize database:**
   ```bash
   docker-compose exec api python -c "from database import init_db; init_db()"
   ```

3. **Run migrations (optional):**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

4. **Seed database (optional):**
   ```bash
   docker-compose exec api python seed.py
   ```

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Jobs

- `POST /jobs` - Create a new job posting
- `GET /jobs/{job_id}` - Get job details
- `POST /jobs/{job_id}/parse` - Parse job description from text
- `GET /jobs/{job_id}/shortlist` - Get shortlisted candidates for a job

### Candidates

- `POST /candidates` - Create a new candidate
- `GET /candidates/{candidate_id}` - Get candidate details
- `POST /candidates/{candidate_id}/resumes` - Upload a resume

### Actions

- `POST /jobs/{job_id}/actions/contact` - Contact a candidate (sends email)

### Feedback

- `POST /feedback` - Submit feedback about a candidate or job

### Audit Logs

- `GET /audit-logs` - Get audit logs (with optional filters)

## Database Models

- **jobs**: Job postings with skills, requirements, etc.
- **candidates**: Candidate information
- **resumes**: Resume files and parsed data
- **scores**: Fit scores between candidates and jobs
- **actions**: Automated actions taken by the system
- **audit_logs**: Complete audit trail of all actions
- **feedback**: User feedback on candidates/jobs

## Background Tasks

Celery tasks run asynchronously:

1. **parse_resume**: Extracts text and parses structured data from resume files
2. **parse_job_description**: Parses job description text to extract structured data
3. **score_resume_against_jobs**: Scores a resume against all active jobs
4. **score_job_against_candidates**: Scores a job against all candidates

## Scoring Algorithm

The scoring system compares:

- **Skills Match**: 70% weight - Matches required skills with candidate skills
- **Experience Match**: 30% weight - Compares years of experience

Returns:
- `fit_score`: 0.0 to 1.0
- `confidence`: Confidence level in the score
- `reasoning`: Human-readable explanation

## Mock Adapters

### Gmail Adapter (`MockGmailAdapter`)

- `send_email()`: Send email (mock)
- `send_contact_email()`: Send contact email to candidate

### Google Calendar Adapter (`MockGoogleCalendarAdapter`)

- `create_event()`: Create calendar event (mock)
- `schedule_interview()`: Schedule interview

In production, replace these with real API integrations.

## Project Structure

```
backend/
├── main.py              # FastAPI application and endpoints
├── database.py          # Database models and configuration
├── celery_app.py        # Celery configuration
├── tasks.py             # Celery background tasks
├── parsers.py           # File parsing utilities
├── scoring.py           # Scoring algorithm
├── adapters.py          # Mock Gmail/Calendar adapters
├── audit.py             # Audit logging utilities
├── config.py            # Configuration constants
├── seed.py              # Database seeding script
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker Compose configuration
├── alembic.ini          # Alembic configuration
└── alembic/             # Database migrations
    ├── env.py
    └── versions/
```

## Development

### Local Development Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export DATABASE_URL="postgresql://recruitment:recruitment123@localhost:5432/recruitment_db"
   export REDIS_URL="redis://localhost:6379/0"
   export CELERY_BROKER_URL="redis://localhost:6379/0"
   export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
   ```

3. **Start PostgreSQL and Redis:**
   ```bash
   docker-compose up db redis
   ```

4. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start API server:**
   ```bash
   uvicorn main:app --reload
   ```

6. **Start Celery worker (in another terminal):**
   ```bash
   celery -A celery_app worker --loglevel=info
   ```

## Testing the API

### Create a Job

```bash
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "We are looking for an experienced Python developer.",
    "company": "Tech Corp",
    "location": "San Francisco, CA",
    "skills": ["python", "fastapi", "postgresql"],
    "employment_type": "full-time"
  }'
```

### Create a Candidate

```bash
curl -X POST "http://localhost:8000/candidates" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
  }'
```

### Upload a Resume

```bash
curl -X POST "http://localhost:8000/candidates/1/resumes" \
  -F "file=@resume.pdf"
```

### Get Shortlist

```bash
curl "http://localhost:8000/jobs/1/shortlist?min_score=0.5"
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `CELERY_BROKER_URL`: Celery broker URL
- `CELERY_RESULT_BACKEND`: Celery result backend URL

## License

MIT

