from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import os
from pathlib import Path

from database import (
    get_db, Job, Candidate, Resume, Score, Action, AuditLog, Feedback, init_db
)
from config import RESUME_UPLOAD_DIR, ALLOWED_RESUME_EXTENSIONS, MAX_FILE_SIZE
from parsers import extract_text_from_file, parse_job_description
from tasks import parse_resume_task, parse_job_description_task
from adapters import gmail_adapter, calendar_adapter
from audit import create_audit_log, log_automated_action

# Import celery_app to ensure tasks are discoverable
from celery_app import celery_app

app = FastAPI(title="Agentic AI Recruitment Manager", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()


# Pydantic models for request/response
class JobCreate(BaseModel):
    title: str
    description: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    requirements: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    employment_type: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    company: Optional[str]
    location: Optional[str]
    skills: Optional[List[str]]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None


class CandidateResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeResponse(BaseModel):
    id: int
    candidate_id: int
    file_name: str
    file_type: str
    parsing_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ScoreResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    resume_id: Optional[int]
    fit_score: float
    confidence: float
    reasoning: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ShortlistResponse(BaseModel):
    job_id: int
    candidates: List[dict]


class ContactRequest(BaseModel):
    candidate_id: int
    message: Optional[str] = None


class FeedbackCreate(BaseModel):
    job_id: Optional[int] = None
    candidate_id: Optional[int] = None
    score_id: Optional[int] = None
    feedback_type: str
    comment: Optional[str] = None
    rating: Optional[int] = None


# Helper function to save uploaded file
def save_upload_file(file: UploadFile, upload_dir: Path) -> Path:
    """Save uploaded file and return the path."""
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {file_ext} not allowed")
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = upload_dir / safe_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        buffer.write(content)
    
    return file_path


# Endpoints

@app.post("/jobs", response_model=JobResponse)
async def create_job(
    job: JobCreate,
    db: Session = Depends(get_db)
):
    """Create a new job posting."""
    db_job = Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    # Create audit log
    create_audit_log(
        db=db,
        action_type="job_created",
        description=f"Job '{job.title}' created",
        job_id=db_job.id
    )
    
    return db_job


@app.post("/jobs/{job_id}/parse")
async def parse_job_from_text(
    job_id: int,
    text: str = Form(...),
    db: Session = Depends(get_db)
):
    """Parse job description from text."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Parse asynchronously
    task = parse_job_description_task.delay(job_id, text)
    
    return {"message": "Job parsing started", "task_id": task.id, "job_id": job_id}


@app.post("/candidates", response_model=CandidateResponse)
async def create_candidate(
    candidate: CandidateCreate,
    db: Session = Depends(get_db)
):
    """Create a new candidate."""
    db_candidate = Candidate(**candidate.dict())
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    
    # Create audit log
    create_audit_log(
        db=db,
        action_type="candidate_created",
        description=f"Candidate '{candidate.first_name} {candidate.last_name}' created",
        candidate_id=db_candidate.id
    )
    
    return db_candidate


@app.post("/candidates/{candidate_id}/resumes", response_model=ResumeResponse)
async def upload_resume(
    candidate_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a resume for a candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Save file
    file_path = save_upload_file(file, RESUME_UPLOAD_DIR)
    file_ext = Path(file.filename).suffix.lower()
    
    # Create resume record
    resume = Resume(
        candidate_id=candidate_id,
        file_path=str(file_path),
        file_name=file.filename,
        file_type=file_ext,
        parsing_status="pending"
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    
    # Create audit log
    create_audit_log(
        db=db,
        action_type="resume_uploaded",
        description=f"Resume '{file.filename}' uploaded for candidate {candidate_id}",
        candidate_id=candidate_id
    )
    
    # Trigger async parsing
    parse_resume_task.delay(resume.id)
    
    return resume


@app.get("/jobs/{job_id}/shortlist", response_model=ShortlistResponse)
async def get_shortlist(
    job_id: int,
    min_score: float = 0.0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get shortlisted candidates for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get scores above threshold, ordered by fit_score
    scores = db.query(Score).filter(
        Score.job_id == job_id,
        Score.fit_score >= min_score
    ).order_by(Score.fit_score.desc()).limit(limit).all()
    
    candidates_data = []
    for score in scores:
        candidate = score.candidate
        candidates_data.append({
            "candidate_id": candidate.id,
            "name": f"{candidate.first_name} {candidate.last_name}",
            "email": candidate.email,
            "fit_score": score.fit_score,
            "confidence": score.confidence,
            "reasoning": score.reasoning,
            "skills_match": score.skills_match
        })
    
    return {
        "job_id": job_id,
        "candidates": candidates_data
    }


@app.post("/jobs/{job_id}/actions/contact")
async def contact_candidate(
    job_id: int,
    request: ContactRequest,
    db: Session = Depends(get_db)
):
    """Contact a candidate for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    if not candidate.email:
        raise HTTPException(status_code=400, detail="Candidate email not available")
    
    # Get the best score for this job-candidate pair
    score = db.query(Score).filter(
        Score.job_id == job_id,
        Score.candidate_id == request.candidate_id
    ).order_by(Score.fit_score.desc()).first()
    
    # Create action record
    action = Action(
        job_id=job_id,
        candidate_id=request.candidate_id,
        action_type="contact",
        status="pending",
        metadata={"message": request.message}
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    
    # Send email via mock adapter
    try:
        email_result = gmail_adapter.send_contact_email(
            candidate_email=candidate.email,
            candidate_name=f"{candidate.first_name} {candidate.last_name}",
            job_title=job.title,
            company_name=job.company or "Our Company"
        )
        
        action.status = "completed"
        action.completed_at = datetime.utcnow()
        action.metadata = {**action.metadata, "email_result": email_result}
        db.commit()
        
        # Create audit log with reasoning
        reasoning = f"Contacted candidate based on fit score: {score.fit_score:.2f}" if score else "Contacted candidate"
        confidence = score.confidence if score else 0.5
        
        log_automated_action(
            db=db,
            action=action,
            reasoning=reasoning,
            confidence=confidence
        )
        
        return {
            "success": True,
            "action_id": action.id,
            "message": "Candidate contacted successfully",
            "email_result": email_result
        }
    except Exception as e:
        action.status = "failed"
        action.metadata = {**action.metadata, "error": str(e)}
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Failed to contact candidate: {str(e)}")


@app.post("/feedback")
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """Submit feedback about a candidate or job."""
    db_feedback = Feedback(**feedback.dict())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    # Create audit log
    create_audit_log(
        db=db,
        action_type="feedback_submitted",
        description=f"Feedback submitted: {feedback.feedback_type}",
        job_id=feedback.job_id,
        candidate_id=feedback.candidate_id,
        metadata={"rating": feedback.rating, "comment": feedback.comment}
    )
    
    return {
        "success": True,
        "feedback_id": db_feedback.id,
        "message": "Feedback submitted successfully"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "recruitment-manager"}


@app.get("/jobs/{job_id}")
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get job details."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate details."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@app.get("/audit-logs")
async def get_audit_logs(
    job_id: Optional[int] = None,
    candidate_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get audit logs."""
    query = db.query(AuditLog)
    
    if job_id:
        query = query.filter(AuditLog.job_id == job_id)
    if candidate_id:
        query = query.filter(AuditLog.candidate_id == candidate_id)
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return logs
