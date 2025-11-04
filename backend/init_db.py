#!/usr/bin/env python
"""Helper script to initialize database and run migrations."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, engine
from sqlalchemy import text

def check_database_connection():
    """Check if database is accessible."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def initialize_database():
    """Initialize database tables."""
    try:
        print("Initializing database...")
        init_db()
        print("✓ Database initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("Checking database connection...")
    if not check_database_connection():
        sys.exit(1)
    
    print("\nInitializing database tables...")
    if not initialize_database():
        sys.exit(1)
    
    print("\n✓ Setup complete!")
    print("\nNext steps:")
    print("1. Run migrations: alembic upgrade head")
    print("2. Seed database: python seed.py")
    print("3. Start API server: uvicorn main:app --reload")
    print("4. Start Celery worker: celery -A celery_app worker --loglevel=info")

