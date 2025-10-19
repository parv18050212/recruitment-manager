from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from loguru import logger

from app.database import get_db
from app.models.job import Job
from app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobAnalysisRequest,
    JobAnalysisResponse
)
from app.agents.job_understanding_agent import JobUnderstandingAgent

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new job posting
    """
    try:
        job = Job(
            title=job_data.title,
            description=job_data.description,
            company_name=job_data.company_name,
            location=job_data.location,
            job_type=job_data.job_type,
            salary_min=job_data.salary_min,
            salary_max=job_data.salary_max,
            currency=job_data.currency,
            is_urgent=job_data.is_urgent,
            status="active"
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Created job: {job.id} - {job.title}")
        return job
        
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """
    List all jobs with optional filtering
    """
    query = db.query(Job)
    
    if status_filter:
        query = query.filter(Job.status == status_filter)
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific job by ID
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a job posting
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Update fields
    update_data = job_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    db.commit()
    db.refresh(job)
    
    logger.info(f"Updated job: {job.id}")
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a job posting
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    db.delete(job)
    db.commit()
    
    logger.info(f"Deleted job: {job_id}")
    return None


@router.post("/analyze", response_model=JobAnalysisResponse)
async def analyze_job(
    request: JobAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a job description using Job Understanding Agent
    This extracts requirements, skills, and creates a structured job profile
    """
    try:
        # Initialize agent
        agent = JobUnderstandingAgent(db=db)
        
        # Analyze job
        result = await agent.analyze_job(request.job_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Analysis failed")
            )
        
        return JobAnalysisResponse(
            success=True,
            job_id=request.job_id,
            job_profile=result["results"].get("profile"),
            requires_clarification=result["results"].get("requires_clarification", []),
            message="Job analyzed successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze job: {str(e)}"
        )


@router.get("/{job_id}/candidates", response_model=List[dict])
async def get_job_candidates(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all candidates for a specific job
    """
    from app.models.candidate import Candidate
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    candidates = db.query(Candidate).filter(Candidate.job_id == job_id).all()
    
    return [
        {
            "id": c.id,
            "full_name": c.full_name,
            "email": c.email,
            "fit_score": c.fit_score,
            "status": c.status,
            "is_shortlisted": c.is_shortlisted
        }
        for c in candidates
    ]