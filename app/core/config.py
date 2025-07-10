from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Any, Dict
import os
from pathlib import Path


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "FastAPI Project"
    PROJECT_DESCRIPTION: str = "A modern FastAPI application with PostgreSQL and JWT authentication"
    PROJECT_VERSION: str = "1.0.0"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Database Settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://fastapi_user:fastapi_password@localhost:5432/fastapi_db",
        env="DATABASE_URL"
    )
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis Settings
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    
    # Security Settings
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        env="SECRET_KEY"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Settings
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000"
    )
    
    # Password Settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_BCRYPT_ROUNDS: int = 12
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Email Settings (optional)
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: Optional[int] = Field(default=None)
    SMTP_USERNAME: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_TLS: bool = Field(default=True)
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIRECTORY: str = "uploads"
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        if not self.ALLOWED_ORIGINS:
            return []
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v):
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    @field_validator("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v
    
    @field_validator("SMTP_PORT", mode="before")
    @classmethod
    def parse_smtp_port(cls, v):
        if v == "" or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_nested_delimiter="__",
        extra="ignore"  # Ignore extra fields from environment
    )


# Create settings instance
settings = Settings()

# Ensure upload directory exists
Path(settings.UPLOAD_DIRECTORY).mkdir(exist_ok=True)