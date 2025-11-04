from sqlalchemy.orm import Session
from database import Job, Candidate, Resume, Score, init_db, engine
from datetime import datetime

# Initialize database
init_db()


def seed_database():
    """Seed the database with initial data."""
    from database import SessionLocal
    
    db: Session = SessionLocal()
    
    try:
        # Create sample jobs
        job1 = Job(
            title="Senior Python Developer",
            description="We are looking for an experienced Python developer with FastAPI and PostgreSQL experience.",
            company="Tech Corp",
            location="San Francisco, CA",
            skills=["python", "fastapi", "postgresql", "docker", "aws"],
            employment_type="full-time",
            status="active"
        )
        
        job2 = Job(
            title="Full Stack Developer",
            description="Full stack developer needed for React and Node.js development.",
            company="StartupXYZ",
            location="Remote",
            skills=["javascript", "react", "node.js", "mongodb", "git"],
            employment_type="full-time",
            status="active"
        )
        
        db.add(job1)
        db.add(job2)
        db.commit()
        db.refresh(job1)
        db.refresh(job2)
        
        print(f"Created jobs: {job1.id}, {job2.id}")
        
        # Create sample candidates
        candidate1 = Candidate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1-555-0101",
            linkedin_url="https://linkedin.com/in/johndoe",
            status="new"
        )
        
        candidate2 = Candidate(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="+1-555-0102",
            linkedin_url="https://linkedin.com/in/janesmith",
            status="new"
        )
        
        db.add(candidate1)
        db.add(candidate2)
        db.commit()
        db.refresh(candidate1)
        db.refresh(candidate2)
        
        print(f"Created candidates: {candidate1.id}, {candidate2.id}")
        
        print("Database seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

