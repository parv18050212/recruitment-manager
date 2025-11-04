from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MockGmailAdapter:
    """Mock adapter for Gmail email sending."""
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str = "recruiter@company.com"
    ) -> Dict:
        """Send an email (mock implementation)."""
        logger.info(f"[MOCK GMAIL] Sending email to {to_email}")
        logger.info(f"[MOCK GMAIL] Subject: {subject}")
        logger.info(f"[MOCK GMAIL] Body: {body[:100]}...")
        
        # In a real implementation, this would use Gmail API
        return {
            "success": True,
            "message_id": f"mock_{datetime.now().timestamp()}",
            "to": to_email,
            "from": from_email,
            "subject": subject,
            "sent_at": datetime.utcnow().isoformat()
        }
    
    def send_contact_email(
        self,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        company_name: str
    ) -> Dict:
        """Send a contact email to a candidate."""
        subject = f"Interest in {job_title} position at {company_name}"
        body = f"""
Dear {candidate_name},

We are impressed with your background and would like to discuss the {job_title} 
position at {company_name} with you.

Please let us know your availability for a call.

Best regards,
Recruitment Team
        """.strip()
        
        return self.send_email(
            to_email=candidate_email,
            subject=subject,
            body=body
        )


class MockGoogleCalendarAdapter:
    """Mock adapter for Google Calendar scheduling."""
    
    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        attendees: list[str],
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict:
        """Create a calendar event (mock implementation)."""
        logger.info(f"[MOCK CALENDAR] Creating event: {title}")
        logger.info(f"[MOCK CALENDAR] Start: {start_time}, End: {end_time}")
        logger.info(f"[MOCK CALENDAR] Attendees: {', '.join(attendees)}")
        
        # In a real implementation, this would use Google Calendar API
        return {
            "success": True,
            "event_id": f"mock_event_{datetime.now().timestamp()}",
            "title": title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "attendees": attendees,
            "description": description,
            "location": location,
            "created_at": datetime.utcnow().isoformat()
        }
    
    def schedule_interview(
        self,
        candidate_email: str,
        candidate_name: str,
        interviewer_email: str,
        interview_time: datetime,
        job_title: str,
        duration_minutes: int = 60
    ) -> Dict:
        """Schedule an interview."""
        end_time = interview_time.replace(
            minute=interview_time.minute + duration_minutes
        )
        
        title = f"Interview: {candidate_name} - {job_title}"
        description = f"Interview with {candidate_name} for {job_title} position"
        
        return self.create_event(
            title=title,
            start_time=interview_time,
            end_time=end_time,
            attendees=[candidate_email, interviewer_email],
            description=description,
            location="Video Call (Link to be sent)"
        )


# Singleton instances
gmail_adapter = MockGmailAdapter()
calendar_adapter = MockGoogleCalendarAdapter()

