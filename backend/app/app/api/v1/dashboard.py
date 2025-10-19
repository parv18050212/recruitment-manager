from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.database import get_db
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.decision import Decision
from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get overall system statistics for dashboard
    """
    try:
        # Job statistics
        total_jobs = db.query(func.count(Job.id)).scalar()
        active_jobs = db.query(func.count(Job.id)).filter(Job.status == "active").scalar()
        urgent_jobs = db.query(func.count(Job.id)).filter(Job.is_urgent == True).scalar()
        
        # Candidate statistics
        total_candidates = db.query(func.count(Candidate.id)).scalar()
        shortlisted_candidates = db.query(func.count(Candidate.id)).filter(
            Candidate.is_shortlisted == True
        ).scalar()
        
        # Status breakdown
        status_counts = db.query(
            Candidate.status,
            func.count(Candidate.id)
        ).group_by(Candidate.status).all()
        
        # Average fit score
        avg_fit_score = db.query(func.avg(Candidate.fit_score)).filter(
            Candidate.fit_score.isnot(None)
        ).scalar()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_candidates = db.query(func.count(Candidate.id)).filter(
            Candidate.created_at >= week_ago
        ).scalar()
        
        recent_decisions = db.query(func.count(Decision.id)).filter(
            Decision.created_at >= week_ago
        ).scalar()
        
        return {
            "jobs": {
                "total": total_jobs,
                "active": active_jobs,
                "urgent": urgent_jobs
            },
            "candidates": {
                "total": total_candidates,
                "shortlisted": shortlisted_candidates,
                "status_breakdown": {status: count for status, count in status_counts},
                "average_fit_score": round(avg_fit_score, 2) if avg_fit_score else None
            },
            "recent_activity": {
                "new_candidates_7d": recent_candidates,
                "decisions_made_7d": recent_decisions
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        )


@router.get("/job/{job_id}/insights")
async def get_job_insights(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed insights for a specific job
    """
    try:
        # Verify job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # Candidate metrics
        total_applicants = db.query(func.count(Candidate.id)).filter(
            Candidate.job_id == job_id
        ).scalar()
        
        shortlisted = db.query(func.count(Candidate.id)).filter(
            Candidate.job_id == job_id,
            Candidate.is_shortlisted == True
        ).scalar()
        
        # Fit score distribution
        score_ranges = [
            ("90-100", 90, 100),
            ("75-89", 75, 89),
            ("60-74", 60, 74),
            ("40-59", 40, 59),
            ("0-39", 0, 39)
        ]
        
        score_distribution = {}
        for label, min_score, max_score in score_ranges:
            count = db.query(func.count(Candidate.id)).filter(
                Candidate.job_id == job_id,
                Candidate.fit_score >= min_score,
                Candidate.fit_score <= max_score
            ).scalar()
            score_distribution[label] = count
        
        # Top candidates
        top_candidates = db.query(Candidate).filter(
            Candidate.job_id == job_id,
            Candidate.fit_score.isnot(None)
        ).order_by(desc(Candidate.fit_score)).limit(10).all()
        
        top_candidates_data = [
            {
                "id": c.id,
                "name": c.full_name,
                "email": c.email,
                "fit_score": c.fit_score,
                "status": c.status,
                "skills": c.skills[:5] if c.skills else []  # Top 5 skills
            }
            for c in top_candidates
        ]
        
        # Skills analysis
        all_candidates = db.query(Candidate).filter(Candidate.job_id == job_id).all()
        skills_frequency = {}
        for candidate in all_candidates:
            if candidate.skills:
                for skill in candidate.skills:
                    skills_frequency[skill] = skills_frequency.get(skill, 0) + 1
        
        # Sort by frequency
        top_skills = sorted(skills_frequency.items(), key=lambda x: x[1], reverse=True)[:15]
        
        return {
            "job_id": job_id,
            "job_title": job.title,
            "metrics": {
                "total_applicants": total_applicants,
                "shortlisted": shortlisted,
                "shortlist_rate": round((shortlisted / total_applicants * 100), 2) if total_applicants > 0 else 0
            },
            "fit_score_distribution": score_distribution,
            "top_candidates": top_candidates_data,
            "skills_analysis": {
                "most_common_skills": [{"skill": skill, "count": count} for skill, count in top_skills]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch job insights: {str(e)}"
        )


@router.get("/agent-activity")
async def get_agent_activity(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get recent agent activity from audit logs
    """
    try:
        recent_logs = db.query(AuditLog).filter(
            AuditLog.event_category == "agent"
        ).order_by(desc(AuditLog.created_at)).limit(limit).all()
        
        activity = [
            {
                "id": log.id,
                "agent_name": log.agent_name,
                "action": log.agent_action,
                "message": log.message,
                "timestamp": log.created_at.isoformat(),
                "severity": log.severity
            }
            for log in recent_logs
        ]
        
        return {
            "total": len(activity),
            "activities": activity
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch agent activity: {str(e)}"
        )


@router.get("/decisions")
async def get_recent_decisions(
    limit: int = 50,
    job_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Get recent AI decisions
    """
    try:
        query = db.query(Decision).order_by(desc(Decision.created_at))
        
        if job_id:
            query = query.filter(Decision.job_id == job_id)
        
        decisions = query.limit(limit).all()
        
        decision_data = []
        for decision in decisions:
            candidate = db.query(Candidate).filter(
                Candidate.id == decision.candidate_id
            ).first()
            
            decision_data.append({
                "id": decision.id,
                "decision_type": decision.decision_type,
                "decision_result": decision.decision_result,
                "candidate_name": candidate.full_name if candidate else "Unknown",
                "reasoning": decision.reasoning,
                "confidence": decision.confidence_score,
                "agent_name": decision.agent_name,
                "timestamp": decision.created_at.isoformat(),
                "hr_approved": decision.hr_approved
            })
        
        return {
            "total": len(decision_data),
            "decisions": decision_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch decisions: {str(e)}"
        )


@router.get("/pipeline/{job_id}")
async def get_recruitment_pipeline(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get recruitment pipeline status for a job
    """
    try:
        # Verify job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # Pipeline stages
        stages = {
            "new": "New Applications",
            "screening": "Screening",
            "under_review": "Under Review",
            "shortlisted": "Shortlisted",
            "contacted": "Contacted",
            "interviewed": "Interviewed",
            "selected": "Selected",
            "rejected": "Rejected"
        }
        
        pipeline_data = {}
        for status, label in stages.items():
            count = db.query(func.count(Candidate.id)).filter(
                Candidate.job_id == job_id,
                Candidate.status == status
            ).scalar()
            
            pipeline_data[status] = {
                "label": label,
                "count": count
            }
        
        return {
            "job_id": job_id,
            "job_title": job.title,
            "pipeline": pipeline_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch pipeline: {str(e)}"
        )