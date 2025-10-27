from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger

from app.agents.base_agent import BaseAgent, ChatPromptTemplate, PydanticOutputParser, Runnable
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.resume_parser import resume_parser


# 1. Define the Pydantic schema for the LLM output
class CandidateAnalysisResult(BaseModel):
    """Pydantic model for candidate-job fit analysis."""
    fit_score: int = Field(description="A score from 0-100 indicating candidate-job fit.", ge=0, le=100)
    confidence: float = Field(description="A score from 0-1 indicating the confidence in the fit_score.", ge=0, le=1)
    matching_skills: List[str] = Field(description="List of required skills that the candidate possesses.")
    missing_skills: List[str] = Field(description="List of required skills the candidate does not have.")
    unique_strengths: List[str] = Field(description="Candidate's unique strengths or standout qualities for this role.")
    concerns: List[str] = Field(description="Any red flags or concerns about the candidate's fit.")
    experience_match: str = Field(description="One of: 'under-qualified', 'qualified', 'over-qualified'")
    education_match: str = Field(description="One of: 'meets requirements', 'exceeds requirements', 'below requirements'")
    reasoning: str = Field(description="Detailed 3-4 sentence explanation of the score and recommendation.")
    recommendation: str = Field(description="One of: 'strong_fit', 'potential_fit', 'weak_fit', 'not_suitable'")


class CandidateIntelligenceAgent(BaseAgent):
    """
    Agent responsible for analyzing candidates and matching them with jobs.
    Uses LangChain with PydanticOutputParser for structured analysis.
    """
    
    def __init__(self, db):
        super().__init__(name="CandidateIntelligenceAgent", db=db)
        self.chain = self._build_chain()

    def _build_chain(self) -> Runnable:
        """Builds the LangChain chain for this agent."""
        
        # 1. Setup the parser
        parser = PydanticOutputParser(pydantic_object=CandidateAnalysisResult)

        # 2. Setup the prompt template
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", """
You are an expert technical recruiter. Analyze the candidate's fit for this job position.
Provide a detailed, unbiased analysis based *only* on the provided job and candidate data.
Follow the JSON schema instructions precisely.

SCORING GUIDELINES:
- 90-100: Exceptional fit, rare find
- 75-89: Strong fit, highly recommended
- 60-74: Good fit, worth considering
- 40-59: Moderate fit, has potential
- 0-39: Weak fit, missing critical requirements
"""),
                ("human", """
Please analyze the following candidate for the given job.

--- JOB POSITION ---
TITLE: {job_title}
REQUIREMENTS:
- Required Skills: {job_req_skills}
- Preferred Skills: {job_pref_skills}
- Experience Required: {job_exp} years
- Education: {job_edu}
- Job Profile: {job_profile}

--- CANDIDATE PROFILE ---
NAME: {candidate_name}
SKILLS: {candidate_skills}
EXPERIENCE: {candidate_exp} years
EDUCATION: {candidate_edu}
WORK HISTORY: {candidate_work_history}
CANDIDATE SUMMARY: {candidate_profile}

{format_instructions}
"""),
            ]
        )
        
        # 3. Return the full chain
        return prompt_template | self.llm | parser

    def _determine_next_steps(self, recommendation: str, fit_score: int) -> List[str]:
        """Determine what actions should be taken based on analysis."""
        next_steps = []
        if recommendation == "strong_fit" or fit_score >= 75:
            next_steps.extend(["Schedule screening call", "Add to priority review list"])
        elif recommendation == "potential_fit" or fit_score >= 60:
            next_steps.extend(["Flag for HR review", "Consider for phone screening"])
        elif fit_score >= 40:
            next_steps.append("Add to secondary candidate pool")
        else:
            next_steps.append("Send polite rejection email (automated)")
        return next_steps

    async def analyze_candidate(
        self,
        candidate_id: str,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Public method to analyze a candidate for a specific job.
        This replaces the old 'execute' loop.
        """
        log_ctx = {"candidate_id": candidate_id, "job_id": job_id}
        self._log_audit("start", f"Starting analysis for candidate {candidate_id} for job {job_id}", log_ctx)
        
        try:
            # 1. PERCEIVE: Load data from DB
            candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            job = self.db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
                
            self._log_audit("perceive", "Loaded candidate and job data from DB", log_ctx)

            # 2. THINK: Run the LangChain chain
            self._log_audit("think", "Running LLM analysis chain...", log_ctx)
            
            analysis_result: CandidateAnalysisResult = await self.chain.ainvoke({
                # Job Info
                "job_title": job.title,
                "job_req_skills": ", ".join(job.required_skills) if job.required_skills else 'Not specified',
                "job_pref_skills": ", ".join(job.preferred_skills) if job.preferred_skills else 'Not specified',
                "job_exp": f"{job.min_experience_years}-{job.max_experience_years}" if job.min_experience_years else 'Not specified',
                "job_edu": job.education_required or 'Not specified',
                "job_profile": str(job.job_profile),
                # Candidate Info
                "candidate_name": candidate.full_name,
                "candidate_skills": ", ".join(candidate.skills) if candidate.skills else 'Not specified',
                "candidate_exp": candidate.experience_years or 0,
                "candidate_edu": str(candidate.education),
                "candidate_work_history": str(candidate.work_history),
                "candidate_profile": str(candidate.candidate_profile),
                # Format Instructions
                "format_instructions": PydanticOutputParser(pydantic_object=CandidateAnalysisResult).get_format_instructions(),
            })
            
            analysis_dict = analysis_result.model_dump()
            self._log_audit("think_complete", "Successfully analyzed candidate", {**log_ctx, "score": analysis_result.fit_score})

            # 3. ACT: Save results back to the DB
            candidate.fit_score = analysis_result.fit_score
            candidate.confidence = analysis_result.confidence
            candidate.reasoning = analysis_result.reasoning
            
            # Merge analysis into candidate_profile JSONB field
            profile_data = candidate.candidate_profile or {}
            profile_data.update({
                "matching_skills": analysis_result.matching_skills,
                "missing_skills": analysis_result.missing_skills,
                "unique_strengths": analysis_result.unique_strengths,
                "concerns": analysis_result.concerns,
                "experience_match": analysis_result.experience_match,
                "education_match": analysis_result.education_match
            })
            candidate.candidate_profile = profile_data
            
            # Update status
            if analysis_result.recommendation == "strong_fit":
                candidate.is_shortlisted = True
                candidate.status = "shortlisted"
            elif analysis_result.recommendation == "potential_fit":
                candidate.status = "under_review"
            else:
                candidate.status = "screening"
            
            self.db.commit()
            self.db.refresh(candidate)
            self._log_audit("act", "Saved analysis results to DB", {**log_ctx, "score": candidate.fit_score})
            
            # 4. Determine next steps
            next_steps = self._determine_next_steps(analysis_result.recommendation, analysis_result.fit_score)
            
            return {
                "success": True,
                "agent": self.name,
                "results": {
                    "status": "analyzed",
                    "candidate_id": candidate.id,
                    "analysis": analysis_dict,
                    "next_steps": next_steps
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Agent {self.name} execution failed: {str(e)}", **log_ctx)
            self.db.rollback()
            self._log_audit("error", f"Execution failed: {str(e)}", {**log_ctx, "error": str(e)}, severity="error")
            return {
                "success": False,
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def bulk_analyze_candidates(
        self,
        job_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple candidates for a job.
        This method remains largely the same, as it just calls
        the newly refactored analyze_candidate method.
        """
        # Get all unscored candidates for this job
        candidates = self.db.query(Candidate).filter(
            Candidate.job_id == job_id,
            Candidate.fit_score.is_(None)
        ).limit(limit).all()
        
        self._log_audit("bulk_start", f"Starting bulk analysis for job {job_id} on {len(candidates)} candidates", {"job_id": job_id, "count": len(candidates)})
        
        results = []
        for candidate in candidates:
            try:
                result = await self.analyze_candidate(candidate.id, job_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze candidate {candidate.id} in bulk: {str(e)}")
                results.append({
                    "success": False,
                    "candidate_id": candidate.id,
                    "error": str(e)
                })
        
        self._log_audit("bulk_complete", f"Finished bulk analysis for job {job_id}", {"job_id": job_id, "processed": len(results)})
        return results