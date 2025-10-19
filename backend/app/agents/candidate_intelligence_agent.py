from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.resume_parser import resume_parser
from loguru import logger


class CandidateIntelligenceAgent(BaseAgent):
    """
    Agent responsible for analyzing candidates and matching them with jobs
    Extracts candidate information, calculates fit scores, and provides reasoning
    """
    
    def __init__(self, db):
        super().__init__(name="CandidateIntelligenceAgent", db=db)
    
    async def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perceive: Load candidate and job data
        
        Args:
            context: Contains candidate_id and job_id
            
        Returns:
            Candidate and job information
        """
        candidate_id = context.get("candidate_id")
        job_id = context.get("job_id")
        resume_path = context.get("resume_path")
        
        # Load candidate
        if candidate_id:
            candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            candidate_data = {
                "id": candidate.id,
                "name": candidate.full_name,
                "email": candidate.email,
                "skills": candidate.skills,
                "experience_years": candidate.experience_years,
                "education": candidate.education,
                "work_history": candidate.work_history,
                "resume_text": candidate.resume_text,
                "candidate_profile": candidate.candidate_profile
            }
        elif resume_path:
            # Parse new resume
            parse_result = await resume_parser.parse_resume(resume_path)
            if not parse_result["success"]:
                raise ValueError(f"Failed to parse resume: {parse_result.get('error')}")
            
            candidate_data = parse_result["structured_data"]
            candidate_data["resume_text"] = parse_result["raw_text"]
        else:
            raise ValueError("Must provide candidate_id or resume_path")
        
        # Load job
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job_data = {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "required_skills": job.required_skills,
            "preferred_skills": job.preferred_skills,
            "min_experience_years": job.min_experience_years,
            "max_experience_years": job.max_experience_years,
            "education_required": job.education_required,
            "job_profile": job.job_profile
        }
        
        return {
            "candidate": candidate_data,
            "job": job_data
        }
    
    async def think(self, perceived_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Think: Analyze candidate-job fit using LLM reasoning
        
        Args:
            perceived_data: Candidate and job data
            
        Returns:
            Analysis plan with fit score and reasoning
        """
        candidate = perceived_data["candidate"]
        job = perceived_data["job"]
        
        # Create analysis prompt
        prompt = f"""
You are an expert technical recruiter. Analyze the candidate's fit for this job position.

JOB POSITION: {job['title']}

JOB REQUIREMENTS:
- Required Skills: {', '.join(job['required_skills']) if job['required_skills'] else 'Not specified'}
- Preferred Skills: {', '.join(job['preferred_skills']) if job['preferred_skills'] else 'Not specified'}
- Experience Required: {job['min_experience_years']}-{job['max_experience_years']} years
- Education: {job['education_required'] or 'Not specified'}

CANDIDATE PROFILE:
Name: {candidate.get('full_name', candidate.get('name', 'Unknown'))}
Skills: {', '.join(candidate['skills']) if candidate['skills'] else 'Not specified'}
Experience: {candidate['experience_years']} years
Education: {candidate['education']}
Work History: {candidate['work_history']}

Analyze the candidate-job fit and return a JSON object with:

{{
    "fit_score": <number 0-100>,
    "confidence": <number 0-1>,
    "matching_skills": [<list of skills that match>],
    "missing_skills": [<list of required skills candidate doesn't have>],
    "unique_strengths": [<candidate's unique strengths or standout qualities>],
    "concerns": [<any red flags or concerns>],
    "experience_match": "<under-qualified|qualified|over-qualified>",
    "education_match": "<meets requirements|exceeds requirements|below requirements>",
    "reasoning": "<detailed 3-4 sentence explanation of the score>",
    "recommendation": "<strong_fit|potential_fit|weak_fit|not_suitable>"
}}

SCORING GUIDELINES:
- 90-100: Exceptional fit, rare find
- 75-89: Strong fit, highly recommended
- 60-74: Good fit, worth considering
- 40-59: Moderate fit, has potential
- 0-39: Weak fit, missing critical requirements
"""
        
        try:
            analysis = await self.ask_llm_json(prompt)
            
            return {
                "action": "analyze_fit",
                "analysis": analysis,
                "next_steps": self._determine_next_steps(analysis)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze candidate fit: {str(e)}")
            raise
    
    async def act(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Act: Save analysis results to candidate record
        
        Args:
            action_plan: Analysis results from think phase
            
        Returns:
            Update results
        """
        analysis = action_plan["analysis"]
        candidate_id = self.state.get("candidate_id")
        
        if candidate_id:
            candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if candidate:
                # Update candidate with analysis
                candidate.fit_score = analysis["fit_score"]
                candidate.confidence = analysis["confidence"]
                candidate.reasoning = analysis["reasoning"]
                candidate.candidate_profile = {
                    "matching_skills": analysis["matching_skills"],
                    "missing_skills": analysis["missing_skills"],
                    "unique_strengths": analysis["unique_strengths"],
                    "concerns": analysis["concerns"],
                    "experience_match": analysis["experience_match"],
                    "education_match": analysis["education_match"]
                }
                
                # Update status based on recommendation
                if analysis["recommendation"] == "strong_fit":
                    candidate.is_shortlisted = True
                    candidate.status = "shortlisted"
                elif analysis["recommendation"] == "potential_fit":
                    candidate.status = "under_review"
                else:
                    candidate.status = "screening"
                
                self.db.commit()
                self.db.refresh(candidate)
                
                return {
                    "status": "analyzed",
                    "candidate_id": candidate.id,
                    "fit_score": candidate.fit_score,
                    "recommendation": analysis["recommendation"],
                    "next_steps": action_plan["next_steps"]
                }
        
        return {
            "status": "analyzed",
            "analysis": analysis,
            "message": "Analysis complete but not saved (no candidate_id)"
        }
    
    async def reflect(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflect: Evaluate quality of analysis
        
        Args:
            results: Analysis results
            
        Returns:
            Quality reflection
        """
        analysis = results.get("analysis", {})
        fit_score = analysis.get("fit_score", 0)
        confidence = analysis.get("confidence", 0)
        
        return {
            "analysis_quality": "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low",
            "decision_clarity": "clear" if fit_score > 75 or fit_score < 40 else "borderline",
            "learnings": [
                f"Candidate scored {fit_score}/100",
                f"Found {len(analysis.get('matching_skills', []))} matching skills",
                f"Identified {len(analysis.get('missing_skills', []))} skill gaps"
            ]
        }
    
    def _determine_next_steps(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Determine what actions should be taken based on analysis
        
        Args:
            analysis: Candidate analysis results
            
        Returns:
            List of recommended next steps
        """
        recommendation = analysis.get("recommendation")
        fit_score = analysis.get("fit_score", 0)
        
        next_steps = []
        
        if recommendation == "strong_fit" or fit_score >= 75:
            next_steps.extend([
                "Send selection email to candidate",
                "Schedule screening call",
                "Add to priority review list"
            ])
        elif recommendation == "potential_fit" or fit_score >= 60:
            next_steps.extend([
                "Flag for HR review",
                "Consider for phone screening",
                "Keep in talent pool"
            ])
        elif fit_score >= 40:
            next_steps.append("Add to secondary candidate pool")
        else:
            next_steps.append("Send polite rejection email")
        
        return next_steps
    
    async def analyze_candidate(
        self,
        candidate_id: str,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Public method to analyze a candidate for a specific job
        
        Args:
            candidate_id: Candidate ID to analyze
            job_id: Job ID to match against
            
        Returns:
            Analysis results
        """
        self.state["candidate_id"] = candidate_id
        self.state["job_id"] = job_id
        
        return await self.execute({
            "candidate_id": candidate_id,
            "job_id": job_id
        })
    
    async def bulk_analyze_candidates(
        self,
        job_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple candidates for a job
        
        Args:
            job_id: Job ID to match against
            limit: Maximum number of candidates to analyze
            
        Returns:
            List of analysis results
        """
        # Get all unscored candidates for this job
        candidates = self.db.query(Candidate).filter(
            Candidate.job_id == job_id,
            Candidate.fit_score.is_(None)
        ).limit(limit).all()
        
        results = []
        for candidate in candidates:
            try:
                result = await self.analyze_candidate(candidate.id, job_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze candidate {candidate.id}: {str(e)}")
                results.append({
                    "success": False,
                    "candidate_id": candidate.id,
                    "error": str(e)
                })
        
        return results