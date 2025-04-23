import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL database configuration
    DATABASE_URL: str = "postgresql://postgres:b2b6e2d0afa36e3adea8@marinho-backpython-pgweb.4oqjah.easypanel.host:5435/marinho?sslmode=disable"
    
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