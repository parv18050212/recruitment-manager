from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models.job import Job
from loguru import logger
import json


class JobUnderstandingAgent(BaseAgent):
    """
    Agent responsible for understanding and structuring job descriptions
    Extracts requirements, skills, and creates a structured job profile
    """
    
    def __init__(self, db):
        super().__init__(name="JobUnderstandingAgent", db=db)
    
    async def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perceive: Read and extract job description
        
        Args:
            context: Contains job_id or raw job description
            
        Returns:
            Structured job data
        """
        job_id = context.get("job_id")
        raw_description = context.get("description")
        
        if job_id:
            # Fetch from database
            job = self.db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            return {
                "job_id": job.id,
                "title": job.title,
                "description": job.description,
                "company": job.company_name,
                "location": job.location,
                "raw_data": {
                    "job_type": job.job_type,
                    "salary_range": f"{job.salary_min}-{job.salary_max}" if job.salary_min else None
                }
            }
        
        elif raw_description:
            # Parse raw text
            return {
                "job_id": None,
                "title": context.get("title", "Unknown Position"),
                "description": raw_description,
                "company": context.get("company"),
                "location": context.get("location"),
                "raw_data": context
            }
        
        else:
            raise ValueError("Must provide job_id or description")
    
    async def think(self, perceived_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Think: Analyze job description using LLM to extract structured requirements
        
        Args:
            perceived_data: Job data from perceive phase
            
        Returns:
            Extraction plan and structured requirements
        """
        description = perceived_data["description"]
        title = perceived_data["title"]
        
        # Define schema for structured extraction
        extraction_schema = {
            "required_skills": ["string"],
            "preferred_skills": ["string"],
            "min_experience_years": "number or null",
            "max_experience_years": "number or null",
            "education_required": "string or null",
            "key_responsibilities": ["string"],
            "soft_skills": ["string"],
            "technical_requirements": ["string"],
            "job_summary": "string"
        }
        
        # Craft prompt for LLM
        prompt = f"""
You are an expert HR analyst. Analyze this job posting and extract structured information.

JOB TITLE: {title}

JOB DESCRIPTION:
{description}

Extract the following information and return as valid JSON:

1. **required_skills**: List of mandatory technical skills (e.g., ["Python", "Django", "PostgreSQL"])
2. **preferred_skills**: List of nice-to-have skills
3. **min_experience_years**: Minimum years of experience required (number or null)
4. **max_experience_years**: Maximum years of experience (number or null)
5. **education_required**: Required education level (e.g., "Bachelor's in Computer Science")
6. **key_responsibilities**: Main job duties (list of strings)
7. **soft_skills**: Required soft skills (e.g., ["Communication", "Leadership"])
8. **technical_requirements**: Specific technical requirements
9. **job_summary**: A concise 2-3 sentence summary of the role

Return ONLY the JSON object, no additional text.
"""
        
        try:
            structured_profile = await self.ask_llm_json(prompt, schema=extraction_schema)
            
            return {
                "action": "extract_and_structure",
                "job_profile": structured_profile,
                "confidence": 0.85,  # Can be computed based on completeness
                "requires_clarification": self._check_missing_info(structured_profile)
            }
            
        except Exception as e:
            logger.error(f"Failed to extract job profile: {str(e)}")
            raise
    
    async def act(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Act: Save structured job profile to database
        
        Args:
            action_plan: Output from think phase with job_profile
            
        Returns:
            Save results
        """
        job_profile = action_plan["job_profile"]
        job_id = self.state.get("current_job_id")
        
        if job_id:
            # Update existing job
            job = self.db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.required_skills = job_profile.get("required_skills", [])
                job.preferred_skills = job_profile.get("preferred_skills", [])
                job.min_experience_years = job_profile.get("min_experience_years")
                job.max_experience_years = job_profile.get("max_experience_years")
                job.education_required = job_profile.get("education_required")
                job.job_profile = job_profile
                
                self.db.commit()
                self.db.refresh(job)
                
                return {
                    "status": "updated",
                    "job_id": job.id,
                    "profile": job_profile,
                    "requires_clarification": action_plan.get("requires_clarification", [])
                }
        
        return {
            "status": "analyzed",
            "profile": job_profile,
            "message": "Job profile created but not saved (no job_id provided)"
        }
    
    async def reflect(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflect: Check quality of extraction
        
        Args:
            results: Output from act phase
            
        Returns:
            Quality assessment
        """
        profile = results.get("profile", {})
        
        # Calculate completeness score
        total_fields = 9
        filled_fields = sum(1 for v in profile.values() if v)
        completeness = filled_fields / total_fields
        
        # Check for critical missing info
        critical_missing = []
        if not profile.get("required_skills"):
            critical_missing.append("required_skills")
        if profile.get("min_experience_years") is None:
            critical_missing.append("experience_requirement")
        
        return {
            "completeness_score": completeness,
            "quality": "high" if completeness > 0.8 else "medium" if completeness > 0.5 else "low",
            "critical_missing": critical_missing,
            "learnings": [
                f"Extracted {len(profile.get('required_skills', []))} required skills",
                f"Identified {len(profile.get('key_responsibilities', []))} responsibilities"
            ]
        }
    
    def _check_missing_info(self, profile: Dict[str, Any]) -> List[str]:
        """
        Check what critical information is missing
        
        Args:
            profile: Extracted job profile
            
        Returns:
            List of missing fields that need clarification
        """
        missing = []
        
        if not profile.get("required_skills"):
            missing.append("What are the required technical skills?")
        
        if profile.get("min_experience_years") is None:
            missing.append("What is the minimum experience required?")
        
        if not profile.get("education_required"):
            missing.append("What educational qualifications are needed?")
        
        return missing
    
    async def analyze_job(self, job_id: str) -> Dict[str, Any]:
        """
        Public method to analyze a job posting
        
        Args:
            job_id: Job ID to analyze
            
        Returns:
            Analysis results
        """
        self.state["current_job_id"] = job_id
        return await self.execute({"job_id": job_id})