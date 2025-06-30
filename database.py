import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_database_url():
    """Get database URL with proper format for SQLAlchemy"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Convert Heroku's postgres:// to postgresql:// for SQLAlchemy 1.4+
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return database_url

# Create engine with the corrected URL
DATABASE_URL = get_database_url()

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    raise ValueError("DATABASE_URL environment variable not set")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from models import Base
    Base.metadata.create_all(bind=engine)