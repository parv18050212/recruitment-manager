from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from loguru import logger
from pathlib import Path
import shutil

from app.database import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.candidate import (
    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    CandidateAnalysisRequest,
    CandidateAnalysisResponse,
    BulkAnalysisRequest
)
from app.agents.candidate_intelligence_agent import CandidateIntelligenceAgent
from app.services.resume_parser import resume_parser
from app.config import settings

router = APIRouter()


@router.post("/upload", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    job_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a resume and automatically parse it
    """
    try:
        # Verify job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Check file type
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_ext} not supported. Allowed: {allowed_extensions}"
            )
        
        # Save file
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{job_id}_{file.filename}"
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved resume: {file_path}")
        
        # Parse resume
        parse_result = await resume_parser.parse_resume(str(file_path))
        
        if not parse_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse resume: {parse_result.get('error')}"
            )
        
        # Create candidate record
        structured_data = parse_result["structured_data"]
        candidate = Candidate(
            job_id=job_id,
            full_name=structured_data.get("full_name", "Unknown"),
            email=structured_data.get("email"),
            phone=structured_data.get("phone"),
            linkedin_url=structured_data.get("linkedin_url"),
            location=structured_data.get("location"),
            resume_file_path=str(file_path),
            resume_text=parse_result["raw_text"],
            skills=structured_data.get("skills", []),
            experience_years=structured_data.get("experience_years"),
            education=structured_data.get("education", []),
            work_history=structured_data.get("work_history", []),
            certifications=structured_data.get("certifications", []),
            achievements=structured_data.get("achievements", []),
            candidate_profile=structured_data,
            status="new"
        )
        
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        logger.info(f"Created candidate: {candidate.id} - {candidate.full_name}")
        return candidate
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload resume: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process resume: {str(e)}"
        )


@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    candidate_data: CandidateCreate,
    db: Session = Depends(get_db)
):
    """
    Manually create a candidate (without resume upload)
    """
    try:
        # Verify job exists
        job = db.query(Job).filter(Job.id == candidate_data.job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {candidate_data.job_id} not found"
            )
        
        candidate = Candidate(
            job_id=candidate_data.job_id,
            full_name=candidate_data.full_name,
            email=candidate_data.email,
            phone=candidate_data.phone,
            linkedin_url=candidate_data.linkedin_url,
            location=candidate_data.location,
            skills=candidate_data.skills,
            experience_years=candidate_data.experience_years,
            education=candidate_data.education,
            work_history=candidate_data.work_history,
            status="new"
        )
        
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        logger.info(f"Created candidate: {candidate.id} - {candidate.full_name}")
        return candidate
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create candidate: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create candidate: {str(e)}"
        )


@router.get("/", response_model=List[CandidateResponse])
async def list_candidates(
    skip: int = 0,
    limit: int = 100,
    job_id: str = None,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """
    List candidates with optional filtering
    """
    query = db.query(Candidate)
    
    if job_id:
        query = query.filter(Candidate.job_id == job_id)
    
    if status_filter:
        query = query.filter(Candidate.status == status_filter)
    
    candidates = query.offset(skip).limit(limit).all()
    return candidates


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific candidate by ID
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found"
        )
    
    return candidate


@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: str,
    candidate_update: CandidateUpdate,
    db: Session = Depends(get_db)
):
    """
    Update candidate information
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found"
        )
    
    # Update fields
    update_data = candidate_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(candidate, field, value)
    
    db.commit()
    db.refresh(candidate)
    
    logger.info(f"Updated candidate: {candidate.id}")
    return candidate


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a candidate
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found"
        )
    
    db.delete(candidate)
    db.commit()
    
    logger.info(f"Deleted candidate: {candidate_id}")
    return None


@router.post("/analyze", response_model=CandidateAnalysisResponse)
async def analyze_candidate(
    request: CandidateAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a candidate's fit for a job using Candidate Intelligence Agent
    """
    try:
        # Initialize agent
        agent = CandidateIntelligenceAgent(db=db)
        
        # Analyze candidate
        result = await agent.analyze_candidate(request.candidate_id, request.job_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Analysis failed")
            )
        
        results_data = result.get("results", {})
        analysis = results_data.get("analysis", {})
        
        return CandidateAnalysisResponse(
            success=True,
            candidate_id=request.candidate_id,
            fit_score=analysis.get("fit_score"),
            recommendation=analysis.get("recommendation"),
            reasoning=analysis.get("reasoning"),
            next_steps=results_data.get("next_steps", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze candidate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze candidate: {str(e)}"
        )


@router.post("/analyze/bulk")
async def bulk_analyze_candidates(
    request: BulkAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze multiple candidates for a job
    """
    try:
        agent = CandidateIntelligenceAgent(db=db)
        results = await agent.bulk_analyze_candidates(request.job_id, request.limit)
        
        return {
            "success": True,
            "job_id": request.job_id,
            "total_analyzed": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk analyze: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk analyze: {str(e)}"
        )