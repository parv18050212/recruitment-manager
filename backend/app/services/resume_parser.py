from typing import Dict, Any, Optional, List
import PyPDF2
import docx
from pathlib import Path
from loguru import logger
import re

from app.config import settings
from pydantic import BaseModel, Field

# LangChain Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable


# --- LangChain Setup (Module Level) ---

# 1. Define the Pydantic schema for the LLM output
class StructuredResume(BaseModel):
    """Pydantic model for structured resume data extraction."""
    full_name: str = Field(description="Candidate's full name")
    email: Optional[str] = Field(description="Email address (if present)", default=None)
    phone: Optional[str] = Field(description="Phone number (if present)", default=None)
    linkedin_url: Optional[str] = Field(description="LinkedIn profile URL (if present)", default=None)
    location: Optional[str] = Field(description="Current location/address", default=None)
    professional_summary: Optional[str] = Field(description="Brief professional summary (2-3 sentences)", default=None)
    skills: List[str] = Field(description="List of all technical and professional skills mentioned", default=[])
    experience_years: Optional[float] = Field(description="Total years of professional experience (calculated from work history)", default=None)
    education: List[Dict[str, Any]] = Field(description="Array of education entries with degree, field, institution, and year", default=[])
    work_history: List[Dict[str, Any]] = Field(description="Array of work experiences with company, role, duration, and key responsibilities", default=[])
    certifications: List[str] = Field(description="List of certifications and licenses", default=[])
    achievements: List[str] = Field(description="Notable achievements, awards, or accomplishments", default=[])
    languages: List[str] = Field(description="Languages the candidate speaks", default=[])

# 2. Initialize the LLM
try:
    _llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3, # Lower temp for consistent JSON
        max_output_tokens=settings.GEMINI_MAX_TOKENS,
        convert_system_message_to_human=True
    )
except Exception as e:
    logger.error(f"Failed to initialize ChatGoogleGenerativeAI for ResumeParser: {e}")
    _llm = None

# 3. Setup the parser
_parser = PydanticOutputParser(pydantic_object=StructuredResume)

# 4. Setup the prompt template
_prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an expert resume parser. Extract structured information from the resume text. Follow the JSON schema format exactly."),
        ("human", """
Please parse the following resume text:

--- RESUME TEXT ---
{resume_text}
--- END RESUME TEXT ---

Extract the information according to the following schema.
For experience_years, calculate the total from all work history entries.
Extract ALL skills mentioned (technical, soft skills, tools, frameworks).

{format_instructions}
"""),
    ]
)

# 5. Build the chain
_resume_parsing_chain: Optional[Runnable] = None
if _llm:
    _resume_parsing_chain = _prompt_template | _llm | _parser
else:
    logger.error("Resume parsing chain could not be built. LLM init failed.")

# --- End LangChain Setup ---


class ResumeParser:
    """Service for parsing and extracting information from resumes"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.doc', '.txt']
        if not _resume_parsing_chain:
            logger.error("ResumeParser is non-functional. The LLM chain failed to initialize.")
    
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
        Use LangChain to extract structured information from resume text
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Structured candidate data (as dict)
        """
        if not _resume_parsing_chain:
            raise RuntimeError("Resume parsing chain is not initialized.")
            
        try:
            # Run the LangChain chain
            structured_data: StructuredResume = await _resume_parsing_chain.ainvoke({
                "resume_text": resume_text,
                "format_instructions": _parser.get_format_instructions()
            })
            
            structured_dict = structured_data.model_dump()
            
            # Post-process: Calculate experience if not provided
            if not structured_dict.get("experience_years") and structured_dict.get("work_history"):
                structured_dict["experience_years"] = self._calculate_total_experience(
                    structured_dict["work_history"]
                )
            
            # Extract email/phone with regex if LLM missed them
            if not structured_dict.get("email"):
                structured_dict["email"] = self._extract_email(resume_text)
            
            if not structured_dict.get("phone"):
                structured_dict["phone"] = self._extract_phone(resume_text)
            
            return structured_dict
            
        except Exception as e:
            logger.error(f"Failed to structure resume with LangChain: {str(e)}")
            raise
    
    def _calculate_total_experience(self, work_history: list) -> float:
        """
        Calculate total years of experience from work history
        """
        total_months = 0
        for job in work_history:
            duration = job.get("duration", "")
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