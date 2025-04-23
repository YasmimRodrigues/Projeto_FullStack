from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.models.base import Base
from app.utils.logger import logger
from config import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database - create tables if they don't exist"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def get_db() -> Session:
    """
    Get database session - dependency for FastAPI endpoints
    
    Yields:
        Session: SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
