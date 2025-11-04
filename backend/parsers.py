import PyPDF2
from docx import Document
from pathlib import Path
import re
from typing import Dict, List, Optional


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    text = ""
    try:
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")
    return text


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise Exception(f"Error reading DOCX: {str(e)}")


def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract text from file based on file type."""
    file_type_lower = file_type.lower()
    
    if file_type_lower == ".pdf":
        return extract_text_from_pdf(file_path)
    elif file_type_lower in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    elif file_type_lower == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def parse_resume_data(text: str) -> Dict:
    """Parse resume text and extract structured data."""
    text_lower = text.lower()
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    email = emails[0] if emails else None
    
    # Extract phone
    phone_pattern = r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}'
    phones = re.findall(phone_pattern, text)
    phone = phones[0] if phones else None
    
    # Extract LinkedIn URL
    linkedin_pattern = r'linkedin\.com/in/[\w-]+'
    linkedin_matches = re.findall(linkedin_pattern, text_lower)
    linkedin_url = linkedin_matches[0] if linkedin_matches else None
    if linkedin_url:
        linkedin_url = "https://" + linkedin_url
    
    # Extract skills (common patterns)
    skills_keywords = [
        "python", "javascript", "java", "c++", "c#", "react", "angular", "vue",
        "node.js", "django", "flask", "fastapi", "postgresql", "mysql", "mongodb",
        "aws", "docker", "kubernetes", "git", "linux", "agile", "scrum",
        "machine learning", "ai", "data science", "sql", "nosql", "redis",
        "graphql", "rest api", "microservices", "devops", "ci/cd"
    ]
    
    found_skills = []
    for skill in skills_keywords:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    
    # Extract experience years (heuristic)
    experience_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'experience[:\s]+(\d+)\+?\s*years?',
    ]
    years_experience = None
    for pattern in experience_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            years_experience = max([int(m) for m in matches])
            break
    
    # Extract education (degrees)
    education_keywords = ["bachelor", "master", "phd", "degree", "diploma", "bs", "ms", "ba", "ma"]
    education = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in education_keywords):
            # Take context around education line
            context = " ".join(lines[max(0, i-1):min(len(lines), i+2)])
            education.append(context.strip())
    
    # Extract name (first line is often name)
    lines = text.split("\n")
    name_parts = lines[0].strip().split() if lines else []
    first_name = name_parts[0] if name_parts else "Unknown"
    last_name = name_parts[-1] if len(name_parts) > 1 else ""
    
    return {
        "email": email,
        "phone": phone,
        "linkedin_url": linkedin_url,
        "skills": list(set(found_skills)),  # Remove duplicates
        "years_experience": years_experience,
        "education": education[:3],  # Limit to top 3
        "raw_text": text,
        "name_candidates": {
            "first_name": first_name,
            "last_name": last_name
        }
    }


def parse_job_description(text: str) -> Dict:
    """Parse job description text and extract structured data."""
    text_lower = text.lower()
    
    # Extract title (often in first few lines)
    lines = text.split("\n")
    title = lines[0].strip() if lines else "Untitled Position"
    
    # Extract company name
    company_patterns = [
        r'company[:\s]+([^\n]+)',
        r'at\s+([A-Z][a-zA-Z\s]+)',
    ]
    company = None
    for pattern in company_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            company = matches[0].strip().title()
            break
    
    # Extract location
    location_patterns = [
        r'location[:\s]+([^\n]+)',
        r'in\s+([A-Z][a-zA-Z\s,]+)',
    ]
    location = None
    for pattern in location_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            location = matches[0].strip()
            break
    
    # Extract required skills
    skills_keywords = [
        "python", "javascript", "java", "c++", "c#", "react", "angular", "vue",
        "node.js", "django", "flask", "fastapi", "postgresql", "mysql", "mongodb",
        "aws", "docker", "kubernetes", "git", "linux", "agile", "scrum",
        "machine learning", "ai", "data science", "sql", "nosql", "redis",
        "graphql", "rest api", "microservices", "devops", "ci/cd"
    ]
    
    found_skills = []
    for skill in skills_keywords:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    
    # Extract salary range
    salary_patterns = [
        r'\$?(\d{1,3}(?:,\d{3})*(?:k|K)?)\s*[-–]\s*\$?(\d{1,3}(?:,\d{3})*(?:k|K)?)',
        r'salary[:\s]+\$?(\d{1,3}(?:,\d{3})*(?:k|K)?)\s*[-–]\s*\$?(\d{1,3}(?:,\d{3})*(?:k|K)?)',
    ]
    salary_min = None
    salary_max = None
    for pattern in salary_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            min_val, max_val = matches[0]
            # Convert k/K to thousands
            def parse_salary(s: str) -> int:
                s = s.replace(",", "").replace("$", "")
                if s.lower().endswith("k"):
                    return int(s[:-1]) * 1000
                return int(s)
            salary_min = parse_salary(min_val)
            salary_max = parse_salary(max_val)
            break
    
    # Extract employment type
    employment_types = ["full-time", "part-time", "contract", "internship", "freelance"]
    employment_type = None
    for emp_type in employment_types:
        if emp_type in text_lower:
            employment_type = emp_type
            break
    
    # Extract years of experience required
    experience_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'experience[:\s]+(\d+)\+?\s*years?',
    ]
    years_experience_required = None
    for pattern in experience_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            years_experience_required = max([int(m) for m in matches])
            break
    
    return {
        "title": title,
        "company": company,
        "location": location,
        "skills": list(set(found_skills)),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "employment_type": employment_type,
        "years_experience_required": years_experience_required,
        "description": text
    }

