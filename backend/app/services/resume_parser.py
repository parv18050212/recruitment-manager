from typing import Dict, Any, Optional
import PyPDF2
import docx
from pathlib import Path
from loguru import logger
from app.services.llm_service import gemini_service
import re


class ResumeParser:
    """Service for parsing and extracting information from resumes"""
    
    def __init__(self):
        self.llm = gemini_service
        self.supported_formats = ['.pdf', '.docx', '.doc', '.txt']
    
    async def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """
        Parse resume and extract structured information
        
        Args:
            file_path: Path to resume file
            
        Returns:
            Structured resume data
        """
        try:
            # Extract text based on file type
            text = self._extract_text(file_path)
            
            if not text or len(text.strip()) < 50:
                raise ValueError("Resume appears to be empty or too short")
            
            # Use LLM to structure the data
            structured_data = await self._structure_resume(text)
            
            return {
                "success": True,
                "raw_text": text,
                "structured_data": structured_data,
                "file_path": file_path
            }
            
        except Exception as e:
            logger.error(f"Failed to parse resume {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def _extract_text(self, file_path: str) -> str:
        """
        Extract text from different file formats
        
        Args:
            file_path: Path to file
            
        Returns:
            Extracted text content
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {extension}")
        
        try:
            if extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif extension in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            elif extension == '.txt':
                return self._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported format: {extension}")
                
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    
    async def _structure_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Use LLM to extract structured information from resume text
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Structured candidate data
        """
        schema = {
            "full_name": "string",
            "email": "string or null",
            "phone": "string or null",
            "linkedin_url": "string or null",
            "location": "string or null",
            "professional_summary": "string or null",
            "skills": ["string"],
            "experience_years": "number or null",
            "education": [
                {
                    "degree": "string",
                    "field": "string",
                    "institution": "string",
                    "year": "number or null"
                }
            ],
            "work_history": [
                {
                    "company": "string",
                    "role": "string",
                    "duration": "string",
                    "responsibilities": ["string"]
                }
            ],
            "certifications": ["string"],
            "achievements": ["string"],
            "languages": ["string"]
        }
        
        prompt = f"""
You are an expert resume parser. Extract structured information from this resume.

RESUME TEXT:
{resume_text}

Extract the following information and return as valid JSON:

1. **full_name**: Candidate's full name
2. **email**: Email address (if present)
3. **phone**: Phone number (if present)
4. **linkedin_url**: LinkedIn profile URL (if present)
5. **location**: Current location/address
6. **professional_summary**: Brief professional summary (2-3 sentences)
7. **skills**: List of all technical and professional skills mentioned
8. **experience_years**: Total years of professional experience (calculate from work history)
9. **education**: Array of education entries with degree, field, institution, and year
10. **work_history**: Array of work experiences with company, role, duration, and key responsibilities
11. **certifications**: List of certifications and licenses
12. **achievements**: Notable achievements, awards, or accomplishments
13. **languages**: Languages the candidate speaks

IMPORTANT:
- For experience_years, calculate the total from all work history entries
- Extract ALL skills mentioned (technical, soft skills, tools, frameworks)
- Be thorough in extracting work responsibilities
- If information is not present, use null or empty array

Return ONLY the JSON object.
"""
        
        try:
            structured_data = await self.llm.generate_json(prompt, schema=schema)
            
            # Post-process: Calculate experience if not provided
            if not structured_data.get("experience_years") and structured_data.get("work_history"):
                structured_data["experience_years"] = self._calculate_total_experience(
                    structured_data["work_history"]
                )
            
            # Extract email if not found by LLM
            if not structured_data.get("email"):
                email = self._extract_email(resume_text)
                if email:
                    structured_data["email"] = email
            
            # Extract phone if not found
            if not structured_data.get("phone"):
                phone = self._extract_phone(resume_text)
                if phone:
                    structured_data["phone"] = phone
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Failed to structure resume: {str(e)}")
            raise
    
    def _calculate_total_experience(self, work_history: list) -> float:
        """
        Calculate total years of experience from work history
        
        Args:
            work_history: List of work experience entries
            
        Returns:
            Total years of experience
        """
        total_months = 0
        
        for job in work_history:
            duration = job.get("duration", "")
            # Parse duration strings like "2 years", "6 months", "2019-2021"
            years = re.findall(r'(\d+)\s*year', duration.lower())
            months = re.findall(r'(\d+)\s*month', duration.lower())
            
            if years:
                total_months += int(years[0]) * 12
            if months:
                total_months += int(months[0])
        
        return round(total_months / 12, 1)
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number using regex"""
        phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
        match = re.search(phone_pattern, text)
        return match.group(0) if match else None


# Singleton instance
resume_parser = ResumeParser()