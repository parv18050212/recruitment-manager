from celery_app import celery_app
from sqlalchemy.orm import Session
from database import SessionLocal, Job, Candidate, Resume, Score
from parsers import extract_text_from_file, parse_resume_data, parse_job_description
from scoring import calculate_fit_score
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="parse_resume")
def parse_resume_task(resume_id: int):
    """Async task to parse a resume file."""
    db: Session = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            logger.error(f"Resume {resume_id} not found")
            return {"success": False, "error": "Resume not found"}
        
        # Update status to processing
        resume.parsing_status = "processing"
        db.commit()
        
        # Extract text from file
        file_path = Path(resume.file_path)
        if not file_path.exists():
            resume.parsing_status = "failed"
            db.commit()
            return {"success": False, "error": "File not found"}
        
        try:
            text = extract_text_from_file(str(file_path), resume.file_type)
            parsed_data = parse_resume_data(text)
            
            # Update resume with parsed data
            resume.raw_text = text
            resume.parsed_data = parsed_data
            resume.parsing_status = "completed"
            
            # Update candidate info if available
            if parsed_data.get("name_candidates"):
                name_data = parsed_data["name_candidates"]
                if not resume.candidate.first_name or resume.candidate.first_name == "Unknown":
                    resume.candidate.first_name = name_data.get("first_name", resume.candidate.first_name)
                if not resume.candidate.last_name:
                    resume.candidate.last_name = name_data.get("last_name", resume.candidate.last_name)
            
            if parsed_data.get("email") and not resume.candidate.email:
                resume.candidate.email = parsed_data["email"]
            
            if parsed_data.get("phone") and not resume.candidate.phone:
                resume.candidate.phone = parsed_data["phone"]
            
            if parsed_data.get("linkedin_url") and not resume.candidate.linkedin_url:
                resume.candidate.linkedin_url = parsed_data["linkedin_url"]
            
            db.commit()
            
            logger.info(f"Successfully parsed resume {resume_id}")
            
            # Trigger scoring for all jobs
            score_resume_against_jobs_task.delay(resume_id)
            
            return {
                "success": True,
                "resume_id": resume_id,
                "parsed_data": parsed_data
            }
        except Exception as e:
            logger.error(f"Error parsing resume {resume_id}: {str(e)}")
            resume.parsing_status = "failed"
            db.commit()
            return {"success": False, "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="parse_job_description")
def parse_job_description_task(job_id: int, text: str = None):
    """Async task to parse a job description."""
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"success": False, "error": "Job not found"}
        
        # If text is provided, parse it
        if text:
            parsed_data = parse_job_description(text)
            
            # Update job with parsed data
            if parsed_data.get("title"):
                job.title = parsed_data["title"]
            if parsed_data.get("company"):
                job.company = parsed_data["company"]
            if parsed_data.get("location"):
                job.location = parsed_data["location"]
            if parsed_data.get("skills"):
                job.skills = parsed_data["skills"]
            if parsed_data.get("salary_min"):
                job.salary_min = parsed_data["salary_min"]
            if parsed_data.get("salary_max"):
                job.salary_max = parsed_data["salary_max"]
            if parsed_data.get("employment_type"):
                job.employment_type = parsed_data["employment_type"]
            
            db.commit()
            
            logger.info(f"Successfully parsed job {job_id}")
            
            # Trigger scoring for all candidates
            score_job_against_candidates_task.delay(job_id)
            
            return {
                "success": True,
                "job_id": job_id,
                "parsed_data": parsed_data
            }
        else:
            return {"success": False, "error": "No text provided"}
    finally:
        db.close()


@celery_app.task(name="score_resume_against_jobs")
def score_resume_against_jobs_task(resume_id: int):
    """Score a resume against all active jobs."""
    db: Session = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume or resume.parsing_status != "completed":
            logger.error(f"Resume {resume_id} not found or not parsed")
            return {"success": False, "error": "Resume not ready"}
        
        candidate = resume.candidate
        parsed_data = resume.parsed_data or {}
        
        # Get all active jobs
        jobs = db.query(Job).filter(Job.status == "active").all()
        
        results = []
        for job in jobs:
            # Calculate score
            job_data = {
                "skills": job.skills or [],
                "years_experience_required": None  # Could add this to Job model
            }
            
            fit_score, confidence, reasoning, details = calculate_fit_score(
                job_data, {}, parsed_data
            )
            
            # Check if score already exists
            existing_score = db.query(Score).filter(
                Score.job_id == job.id,
                Score.candidate_id == candidate.id,
                Score.resume_id == resume_id
            ).first()
            
            if existing_score:
                existing_score.fit_score = fit_score
                existing_score.confidence = confidence
                existing_score.reasoning = reasoning
                existing_score.skills_match = details.get("skill_details")
                db.commit()
                results.append({"job_id": job.id, "score_id": existing_score.id, "fit_score": fit_score})
            else:
                # Create new score
                score = Score(
                    job_id=job.id,
                    candidate_id=candidate.id,
                    resume_id=resume_id,
                    fit_score=fit_score,
                    confidence=confidence,
                    reasoning=reasoning,
                    skills_match=details.get("skill_details")
                )
                db.add(score)
                db.commit()
                db.refresh(score)
                results.append({"job_id": job.id, "score_id": score.id, "fit_score": fit_score})
        
        logger.info(f"Scored resume {resume_id} against {len(jobs)} jobs")
        return {"success": True, "results": results}
    finally:
        db.close()


@celery_app.task(name="score_job_against_candidates")
def score_job_against_candidates_task(job_id: int):
    """Score a job against all candidates with parsed resumes."""
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"success": False, "error": "Job not found"}
        
        job_data = {
            "skills": job.skills or [],
            "years_experience_required": None
        }
        
        # Get all candidates with completed resumes
        resumes = db.query(Resume).filter(Resume.parsing_status == "completed").all()
        
        results = []
        for resume in resumes:
            candidate = resume.candidate
            parsed_data = resume.parsed_data or {}
            
            # Calculate score
            fit_score, confidence, reasoning, details = calculate_fit_score(
                job_data, {}, parsed_data
            )
            
            # Check if score already exists
            existing_score = db.query(Score).filter(
                Score.job_id == job.id,
                Score.candidate_id == candidate.id,
                Score.resume_id == resume.id
            ).first()
            
            if existing_score:
                existing_score.fit_score = fit_score
                existing_score.confidence = confidence
                existing_score.reasoning = reasoning
                existing_score.skills_match = details.get("skill_details")
                db.commit()
                results.append({"candidate_id": candidate.id, "score_id": existing_score.id, "fit_score": fit_score})
            else:
                # Create new score
                score = Score(
                    job_id=job.id,
                    candidate_id=candidate.id,
                    resume_id=resume.id,
                    fit_score=fit_score,
                    confidence=confidence,
                    reasoning=reasoning,
                    skills_match=details.get("skill_details")
                )
                db.add(score)
                db.commit()
                db.refresh(score)
                results.append({"candidate_id": candidate.id, "score_id": score.id, "fit_score": fit_score})
        
        logger.info(f"Scored job {job_id} against {len(resumes)} candidates")
        return {"success": True, "results": results}
    finally:
        db.close()

