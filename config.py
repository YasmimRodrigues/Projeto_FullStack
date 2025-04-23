import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL database configuration
    DATABASE_URL: str = os.environ.get("DATABASE_URL")
    # If DATABASE_URL is not provided, construct it from individual credentials
    if not DATABASE_URL:
        PGUSER: str = os.environ.get("PGUSER", "postgres")
        PGPASSWORD: str = os.environ.get("PGPASSWORD", "postgres")
        PGHOST: str = os.environ.get("PGHOST", "localhost")
        PGPORT: str = os.environ.get("PGPORT", "5432")
        PGDATABASE: str = os.environ.get("PGDATABASE", "postgres")
        DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
    
    # JWT configuration
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging configuration
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    
    # Application configuration
    APP_NAME: str = "FastAPI Login System"
    API_PREFIX: str = "/api"
    
    class Config:
        case_sensitive = True

settings = Settings()
