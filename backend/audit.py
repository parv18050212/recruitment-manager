from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import logging

from database import AuditLog, Action

logger = logging.getLogger(__name__)


def create_audit_log(
    db: Session,
    action_type: str,
    description: str,
    reasoning: Optional[str] = None,
    confidence: Optional[float] = None,
    job_id: Optional[int] = None,
    candidate_id: Optional[int] = None,
    action_id: Optional[int] = None,
    metadata: Optional[dict] = None
):
    """Create an audit log entry."""
    audit_log = AuditLog(
        action_type=action_type,
        description=description,
        reasoning=reasoning,
        confidence=confidence,
        job_id=job_id,
        candidate_id=candidate_id,
        action_id=action_id,
        metadata=metadata or {}
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    logger.info(f"Audit log created: {action_type} - {description}")
    return audit_log


def log_automated_action(
    db: Session,
    action: Action,
    reasoning: str,
    confidence: float
):
    """Log an automated action with reasoning and confidence."""
    return create_audit_log(
        db=db,
        action_type=f"automated_{action.action_type}",
        description=f"Automated {action.action_type} action executed",
        reasoning=reasoning,
        confidence=confidence,
        job_id=action.job_id,
        candidate_id=action.candidate_id,
        action_id=action.id,
        metadata={
            "action_status": action.status,
            "action_metadata": action.metadata
        }
    )

