from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Union
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ODS"
    APP_VERSION: str = "1.0.1"
    DEBUG: bool = True
    
    # Database - Environment variable takes precedence
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:////app/data/app.db")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str = "dev-secret-key-for-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, description="Refresh token expiration in days")
    
    @field_validator('ACCESS_TOKEN_EXPIRE_MINUTES', 'REFRESH_TOKEN_EXPIRE_DAYS', mode='before')
    @classmethod
    def parse_int_or_default(cls, v, info):
        """Handle empty strings and invalid values by returning the default"""
        if v == '' or v is None:
            # Return the field's default value
            if info.field_name == 'ACCESS_TOKEN_EXPIRE_MINUTES':
                return 60
            elif info.field_name == 'REFRESH_TOKEN_EXPIRE_DAYS':
                return 30
        try:
            return int(v)
        except (ValueError, TypeError):
            # Return default if parsing fails
            if info.field_name == 'ACCESS_TOKEN_EXPIRE_MINUTES':
                return 60
            elif info.field_name == 'REFRESH_TOKEN_EXPIRE_DAYS':
                return 30
        return v
    
    # Session Management
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_BLOCK_DURATION_MINUTES: int = 15
    MAX_REQUESTS_PER_MINUTE: int = 60
    SESSION_CLEANUP_ENABLED: bool = True
    AUTO_REFRESH_BEFORE_EXPIRY_MINUTES: int = 5  # Refresh 5 min before expiry
    MAX_CONCURRENT_SESSIONS_PER_USER: int = 5  # Maximum concurrent sessions per user
    
    # Security - Cookie Settings
    COOKIE_SECURE: bool = True  # Set to True in production (requires HTTPS)
    COOKIE_HTTPONLY: bool = True  # Prevents JavaScript access to cookies
    COOKIE_SAMESITE: str = "none"  # Use "none" for cross-origin cookies (requires Secure=True)
    COOKIE_DOMAIN: Union[str, None] = None  # None allows cookies to work across different origins
    
    # Security - CSRF Protection
    CSRF_TOKEN_EXPIRE_MINUTES: int = 60  # CSRF token expiration
    CSRF_COOKIE_NAME: str = "csrf_token"
    CSRF_HEADER_NAME: str = "X-CSRF-Token"
    
    # CORS configuration removed for testing
    # CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "https://ods-frontend-302004244593.asia-south1.run.app"]
    # ALLOWED_HOSTS: Union[List[str], str] = ["localhost", "127.0.0.1"]
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_EXTENSIONS: Union[List[str], str] = [".xlsx", ".xls"]
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Email (Optional)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@ods.com"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()