import os
from pathlib import Path

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

RESUME_UPLOAD_DIR = UPLOAD_DIR / "resumes"
RESUME_UPLOAD_DIR.mkdir(exist_ok=True)

JOB_UPLOAD_DIR = UPLOAD_DIR / "jobs"
JOB_UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx", ".doc"}
ALLOWED_JOB_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

