# 🤖 AI Recruitment Manager - Agentic Backend

An autonomous AI-powered recruitment system that intelligently manages the entire hiring pipeline using Google Gemini and agentic AI principles.

## 🌟 Features

### Core Capabilities
- ✅ **Autonomous Job Analysis** - Automatically extracts requirements from job descriptions
- ✅ **Intelligent Resume Parsing** - Supports PDF, DOCX, TXT formats
- ✅ **AI-Powered Candidate Screening** - Uses Gemini to match candidates with jobs
- ✅ **Automated Scoring & Ranking** - Calculates fit scores with reasoning
- ✅ **Agentic Decision Making** - Self-directed agents that perceive, think, act, reflect, and adapt
- ✅ **Audit Logging** - Complete transparency of all agent actions
- ✅ **Dashboard Analytics** - Real-time insights and pipeline visualization

### Agentic Architecture
The system implements a **Perceive → Think → Act → Reflect → Adapt** loop with specialized agents:

1. **Job Understanding Agent** - Analyzes job postings and extracts structured requirements
2. **Candidate Intelligence Agent** - Evaluates candidates and calculates fit scores
3. **Decision Making Agent** - Makes hiring recommendations (coming soon)
4. **Communication Agent** - Handles email automation (coming soon)
5. **Scheduling Agent** - Manages interview scheduling (coming soon)
6. **Audit Agent** - Logs and monitors all system activities

## 🏗️ Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Task Queue**: Celery + Celery Beat
- **AI/LLM**: Google Gemini API
- **Monitoring**: Flower (Celery monitoring)
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd recruitment-agent
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Required
GEMINI_API_KEY="your-gemini-api-key-here"
SECRET_KEY="your-secret-key-change-this"

# Optional (for Google integrations)
GOOGLE_CLIENT_ID="your-client-id"
GOOGLE_CLIENT_SECRET="your-client-secret"
GMAIL_SENDER_EMAIL="your-email@gmail.com"
```

### 3. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### 4. Initialize Database

The database will be automatically initialized on first startup. Tables are created via SQLAlchemy models.

### 5. Access the Application

- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health
- **Celery Monitoring (Flower)**: http://localhost:5555

## 📚 API Usage

### Create a Job

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "We are looking for an experienced Python developer with 5+ years experience in Django, FastAPI, and PostgreSQL...",
    "company_name": "Tech Corp",
    "location": "Remote",
    "job_type": "Full-time",
    "salary_min": 80000,
    "salary_max": 120000
  }'
```

### Analyze Job (Extract Requirements)

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "<job-id-from-previous-step>"
  }'
```

### Upload Resume

```bash
curl -X POST "http://localhost:8000/api/v1/candidates/upload?job_id=<job-id>" \
  -F "file=@/path/to/resume.pdf"
```

### Analyze Candidate

```bash
curl -X POST "http://localhost:8000/api/v1/candidates/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "<candidate-id>",
    "job_id": "<job-id>"
  }'
```

### Get Dashboard Stats

```bash
curl "http://localhost:8000/api/v1/dashboard/stats"
```

## 🤖 Autonomous Agent System

The system runs autonomous loops via Celery Beat:

### Scheduled Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `autonomous-agent-loop` | Every 5 minutes | Main agent loop - analyzes new jobs and screens candidates |
| `process-new-candidates` | Every 10 minutes | Processes newly uploaded resumes |
| `generate-daily-report` | Daily at 9 AM | Creates daily summary report |
| `cleanup-old-logs` | Weekly (Sunday 2 AM) | Cleans up old audit logs |

### Manual Task Triggers

You can manually trigger tasks via Python:

```python
from app.tasks.agent_orchestrator import analyze_job_async, bulk_screen_candidates

# Analyze a job asynchronously
analyze_job_async.delay(job_id="<job-id>")

# Bulk screen all candidates for a job
bulk_screen_candidates.delay(job_id="<job-id>", limit=50)
```

## 📊 Project Structure

```
recruitment-agent/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py              # Configuration
│   ├── database.py            # Database setup
│   ├── models/                # SQLAlchemy models
│   │   ├── job.py
│   │   ├── candidate.py
│   │   ├── decision.py
│   │   └── audit_log.py
│   ├── schemas/               # Pydantic schemas
│   │   ├── job.py
│   │   └── candidate.py
│   ├── agents/                # Agentic AI components
│   │   ├── base_agent.py
│   │   ├── job_understanding_agent.py
│   │   └── candidate_intelligence_agent.py
│   ├── services/              # Business logic services
│   │   ├── llm_service.py
│   │   └── resume_parser.py
│   ├── api/v1/                # API routes
│   │   ├── jobs.py
│   │   ├── candidates.py
│   │   └── dashboard.py
│   └── tasks/                 # Celery tasks
│       ├── celery_app.py
│       ├── agent_orchestrator.py
│       └── periodic_tasks.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## 🧪 Development

### Run Locally (Without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (via Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
docker run -d -p 6379:6379 redis:7-alpine

# Run migrations (auto-creates tables)
python -c "from app.database import init_db; init_db()"

# Start FastAPI
uvicorn app.main:app --reload

# In another terminal, start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# In another terminal, start Celery beat
celery -A app.tasks.celery_app beat --loglevel=info
```

### Run Tests

```bash
pytest tests/ -v
```

## 🔧 Configuration Options

Key configuration options in `.env`:

```env
# Agent Behavior
AGENT_LOOP_INTERVAL=300        # Seconds between agent loops
AUTO_SEND_EMAILS=False         # Enable automatic email sending
CONFIDENCE_THRESHOLD=0.75      # Minimum confidence for auto-actions

# LLM Settings
GEMINI_MODEL="gemini-2.0-flash-exp"  # or "gemini-1.5-pro"
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=2048

# File Upload
MAX_UPLOAD_SIZE=10485760       # 10MB in bytes
```

## 📈 Monitoring & Debugging

### View Celery Tasks

Access Flower at http://localhost:5555 to monitor:
- Active tasks
- Task history
- Worker status
- Task rates

### Check Audit Logs

```bash
curl "http://localhost:8000/api/v1/dashboard/agent-activity?limit=50"
```

### Database Access

```bash
docker exec -it recruitment_db psql -U postgres -d recruitment_db
```

## 🚧 Coming Soon

- [ ] **Communication Agent** - Automated email sending
- [ ] **Scheduling Agent** - Interview scheduling with Google Calendar
- [ ] **Feedback Learning** - Agent improvement based on HR feedback
- [ ] **Multi-job Management** - Handle multiple roles simultaneously
- [ ] **Webhook Integration** - Real-time notifications
- [ ] **Advanced Analytics** - ML-based insights

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 💡 Support

For issues and questions:
- Create an issue on GitHub
- Check the [API Documentation](http://localhost:8000/api/docs)
- Review audit logs for debugging

## 🎯 Example Workflow

```bash
# 1. Create a job
JOB_ID=$(curl -s -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "Content-Type: application/json" \
  -d '{"title":"Python Developer","description":"5+ years Python..."}' | jq -r '.id')

# 2. Analyze job requirements
curl -X POST "http://localhost:8000/api/v1/jobs/analyze" \
  -H "Content-Type: application/json" \
  -d "{\"job_id\":\"$JOB_ID\"}"

# 3. Upload resumes
curl -X POST "http://localhost:8000/api/v1/candidates/upload?job_id=$JOB_ID" \
  -F "file=@resume1.pdf"

# 4. Wait for autonomous agent to screen (or trigger manually)
# The agent runs every 5 minutes automatically

# 5. Check results
curl "http://localhost:8000/api/v1/dashboard/job/$JOB_ID/insights"
```

---

**Built with ❤️ using FastAPI, Gemini AI, and Agentic Design Principles**