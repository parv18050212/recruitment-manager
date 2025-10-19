from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class JobCreate(BaseModel):
    """Schema for creating a new job"""
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    company_name: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None  # Full-time, Part-time, Contract
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "INR"
    is_urgent: bool = False


class JobUpdate(BaseModel):
    """Schema for updating a job"""
    title: Optional[str] = None
    description: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    status: Optional[str] = None
    is_urgent: Optional[bool] = None


class JobResponse(BaseModel):
    """Schema for job response"""
    id: str
    title: str
    description: str
    company_name: Optional[str]
    location: Optional[str]
    job_type: Optional[str]
    required_skills: List[str]
    preferred_skills: List[str]
    min_experience_years: Optional[int]
    max_experience_years: Optional[int]
    education_required: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    currency: str
    status: str
    is_urgent: bool
    job_profile: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class JobAnalysisRequest(BaseModel):
    """Request to analyze a job description"""
    job_id: str


class JobAnalysisResponse(BaseModel):
    """Response from job analysis"""
    success: bool
    job_id: str
    job_profile: Optional[Dict[str, Any]]
    requires_clarification: List[str]
    message: Optional[str]