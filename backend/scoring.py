from typing import Dict, List, Tuple
import re


def normalize_skill(skill: str) -> str:
    """Normalize skill names for comparison."""
    skill = skill.lower().strip()
    # Normalize common variations
    replacements = {
        "nodejs": "node.js",
        "node js": "node.js",
        "reactjs": "react",
        "react js": "react",
        "vuejs": "vue",
        "vue js": "vue",
        "angularjs": "angular",
        "angular js": "angular",
        "postgres": "postgresql",
        "postgres sql": "postgresql",
        "mongo": "mongodb",
        "mongo db": "mongodb",
        "ai": "machine learning",
        "ml": "machine learning",
    }
    for old, new in replacements.items():
        if old in skill:
            skill = skill.replace(old, new)
    return skill


def calculate_skill_match(job_skills: List[str], candidate_skills: List[str]) -> Tuple[float, Dict]:
    """Calculate skill matching score between job and candidate."""
    if not job_skills:
        return 0.0, {}
    
    # Normalize skills
    normalized_job_skills = [normalize_skill(s) for s in job_skills]
    normalized_candidate_skills = [normalize_skill(s) for s in candidate_skills]
    
    # Find matches
    matched_skills = []
    unmatched_skills = []
    
    for job_skill in normalized_job_skills:
        # Check exact match
        if job_skill in normalized_candidate_skills:
            matched_skills.append(job_skill)
        else:
            # Check partial match
            found = False
            for candidate_skill in normalized_candidate_skills:
                if job_skill in candidate_skill or candidate_skill in job_skill:
                    matched_skills.append(job_skill)
                    found = True
                    break
            if not found:
                unmatched_skills.append(job_skill)
    
    # Calculate score: matched skills / total required skills
    match_score = len(matched_skills) / len(normalized_job_skills) if normalized_job_skills else 0.0
    
    # Calculate confidence based on match quality
    confidence = match_score
    if len(matched_skills) == len(normalized_job_skills):
        confidence = 1.0
    elif match_score >= 0.7:
        confidence = 0.8
    elif match_score >= 0.5:
        confidence = 0.6
    else:
        confidence = 0.4
    
    return match_score, {
        "matched_skills": matched_skills,
        "unmatched_skills": unmatched_skills,
        "match_count": len(matched_skills),
        "total_required": len(normalized_job_skills),
        "match_percentage": match_score * 100
    }


def calculate_experience_match(
    job_years_required: int | None,
    candidate_years: int | None
) -> Tuple[float, str]:
    """Calculate experience matching score."""
    if not job_years_required:
        return 0.7, "No experience requirement specified"
    
    if not candidate_years:
        return 0.3, "Candidate experience not found"
    
    if candidate_years >= job_years_required:
        return 1.0, f"Meets requirement ({candidate_years} >= {job_years_required} years)"
    elif candidate_years >= job_years_required * 0.7:
        return 0.7, f"Close match ({candidate_years} vs {job_years_required} years)"
    elif candidate_years >= job_years_required * 0.5:
        return 0.5, f"Partial match ({candidate_years} vs {job_years_required} years)"
    else:
        return 0.2, f"Below requirement ({candidate_years} < {job_years_required} years)"


def calculate_fit_score(
    job_data: Dict,
    candidate_data: Dict,
    resume_data: Dict
) -> Tuple[float, float, str, Dict]:
    """
    Calculate overall fit score between candidate and job.
    
    Returns:
        (fit_score, confidence, reasoning, details)
    """
    # Extract skills
    job_skills = job_data.get("skills", [])
    candidate_skills = resume_data.get("skills", [])
    
    # Calculate skill match
    skill_score, skill_details = calculate_skill_match(job_skills, candidate_skills)
    
    # Calculate experience match
    job_years = job_data.get("years_experience_required")
    candidate_years = resume_data.get("years_experience")
    experience_score, experience_reason = calculate_experience_match(job_years, candidate_years)
    
    # Weighted score calculation
    # Skills: 70% weight, Experience: 30% weight
    fit_score = (skill_score * 0.7) + (experience_score * 0.3)
    
    # Calculate confidence
    # Base confidence on how complete the data is
    confidence_factors = []
    
    if job_skills:
        confidence_factors.append(0.3)
    if candidate_skills:
        confidence_factors.append(0.3)
    if job_years is not None:
        confidence_factors.append(0.2)
    if candidate_years is not None:
        confidence_factors.append(0.2)
    
    confidence = sum(confidence_factors) if confidence_factors else 0.5
    
    # Adjust confidence based on match quality
    if fit_score >= 0.8:
        confidence = min(confidence + 0.2, 1.0)
    elif fit_score >= 0.6:
        confidence = min(confidence + 0.1, 1.0)
    elif fit_score < 0.4:
        confidence = max(confidence - 0.1, 0.3)
    
    # Build reasoning
    reasoning_parts = []
    
    if skill_details["matched_skills"]:
        reasoning_parts.append(
            f"Matched {skill_details['match_count']}/{skill_details['total_required']} "
            f"required skills: {', '.join(skill_details['matched_skills'][:5])}"
        )
    else:
        reasoning_parts.append("No matching skills found")
    
    if skill_details["unmatched_skills"]:
        reasoning_parts.append(
            f"Missing skills: {', '.join(skill_details['unmatched_skills'][:5])}"
        )
    
    reasoning_parts.append(experience_reason)
    
    reasoning = ". ".join(reasoning_parts)
    
    # Details dictionary
    details = {
        "skill_score": skill_score,
        "experience_score": experience_score,
        "skill_details": skill_details,
        "experience_reason": experience_reason,
        "fit_score": fit_score,
        "confidence": confidence
    }
    
    return fit_score, confidence, reasoning, details

