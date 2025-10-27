from typing import Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger

from app.agents.base_agent import BaseAgent, ChatPromptTemplate, PydanticOutputParser, Runnable
from app.models.job import Job


# 1. Define the Pydantic schema for the LLM output
class StructuredJobProfile(BaseModel):
    """Pydantic model for structured job profile extraction."""
    required_skills: List[str] = Field(description="List of mandatory technical skills (e.g., ['Python', 'Django', 'PostgreSQL'])")
    preferred_skills: List[str] = Field(description="List of nice-to-have skills")
    min_experience_years: Optional[int] = Field(description="Minimum years of experience required (number or null)")
    max_experience_years: Optional[int] = Field(description="Maximum years of experience (number or null)")
    education_required: Optional[str] = Field(description="Required education level (e.g., \"Bachelor's in Computer Science\")")
    key_responsibilities: List[str] = Field(description="Main job duties (list of strings)")
    soft_skills: List[str] = Field(description="Required soft skills (e.g., ['Communication', 'Leadership'])")
    technical_requirements: List[str] = Field(description="Specific technical requirements or tools mentioned")
    job_summary: str = Field(description="A concise 2-3 sentence summary of the role")


class JobUnderstandingAgent(BaseAgent):
    """
    Agent responsible for understanding and structuring job descriptions
    Uses LangChain with PydanticOutputParser for structured extraction.
    """
    
    def __init__(self, db):
        super().__init__(name="JobUnderstandingAgent", db=db)
        self.chain = self._build_chain()
    
    def _build_chain(self) -> Runnable:
        """Builds the LangChain chain for this agent."""
        
        # 1. Setup the parser
        parser = PydanticOutputParser(pydantic_object=StructuredJobProfile)

        # 2. Setup the prompt template
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an expert HR analyst. Analyze the job posting and extract structured information. You must follow the provided JSON schema format."),
                ("human", """
Analyze this job posting.

JOB TITLE: {title}

JOB DESCRIPTION:
{description}

{format_instructions}
"""),
            ]
        )
        
        # 3. Return the full chain
        return prompt_template | self.llm | parser

    def _check_missing_info(self, profile: StructuredJobProfile) -> List[str]:
        """Check what critical information is missing."""
        missing = []
        if not profile.required_skills:
            missing.append("What are the required technical skills?")
        if profile.min_experience_years is None:
            missing.append("What is the minimum experience required?")
        if not profile.education_required:
            missing.append("What educational qualifications are needed?")
        return missing

    async def analyze_job(self, job_id: str) -> Dict[str, Any]:
        """
        Public method to analyze a job posting.
        This replaces the old 'execute' loop.
        
        Args:
            job_id: Job ID to analyze
            
        Returns:
            Analysis results
        """
        self._log_audit("start", f"Starting analysis for job_id: {job_id}", {"job_id": job_id})
        
        try:
            # 1. PERCEIVE: Load data from DB
            job = self.db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            self._log_audit("perceive", "Loaded job description from DB", {"job_id": job_id})

            # 2. THINK: Run the LangChain chain
            self._log_audit("think", "Running LLM extraction chain...", {"job_id": job_id})
            
            structured_profile: StructuredJobProfile = await self.chain.ainvoke({
                "title": job.title,
                "description": job.description,
                "format_instructions": PydanticOutputParser(pydantic_object=StructuredJobProfile).get_format_instructions(),
            })
            
            profile_dict = structured_profile.model_dump()
            self._log_audit("think_complete", "Successfully extracted job profile", profile_dict)

            # 3. ACT: Save results back to the DB
            job.required_skills = structured_profile.required_skills
            job.preferred_skills = structured_profile.preferred_skills
            job.min_experience_years = structured_profile.min_experience_years
            job.max_experience_years = structured_profile.max_experience_years
            job.education_required = structured_profile.education_required
            job.job_profile = profile_dict
            
            self.db.commit()
            self.db.refresh(job)
            self._log_audit("act", "Saved structured profile to DB", {"job_id": job.id})
            
            # 4. REFLECT (Simplified)
            clarifications = self._check_missing_info(structured_profile)
            
            return {
                "success": True,
                "agent": self.name,
                "results": {
                    "status": "updated",
                    "job_id": job.id,
                    "profile": profile_dict,
                    "requires_clarification": clarifications
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Agent {self.name} execution failed for job {job_id}: {str(e)}")
            self.db.rollback()
            self._log_audit("error", f"Execution failed: {str(e)}", {"error": str(e), "job_id": job_id}, severity="error")
            return {
                "success": False,
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }