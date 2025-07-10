from typing import List, Optional, Any
from pydantic import AnyHttpUrl, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings using Pydantic BaseSettings for environment management.
    Supports .env files and environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=True,
    )

    # Application Settings
    APP_NAME: str = "Rental Management System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Rental Management API"
    
    # Database Settings - SQLite Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    DATABASE_ECHO: bool = False
    
    # Test Database
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    
    # Security Settings (removed auth-specific settings)
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Redis Cache Settings (disabled for SQLite-only setup)
    REDIS_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_TIMEOUT: int = 5
    CACHE_TTL: int = 300  # 5 minutes default
    
    # Email Settings (for notifications)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Pagination Settings
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"]
    
    # Business Rules Settings
    DEFAULT_TAX_RATE: float = 0.08  # 8% default tax
    DEFAULT_LATE_FEE_RATE: float = 0.10  # 10% late fee
    MIN_RENTAL_DAYS: int = 1
    MAX_RENTAL_DAYS: int = 365
    DEFAULT_CURRENCY: str = "USD"
    
    # System Settings
    TIMEZONE: str = "UTC"
    DATE_FORMAT: str = "%Y-%m-%d"
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance Settings
    QUERY_TIMEOUT: int = 30  # seconds
    REQUEST_TIMEOUT: int = 60  # seconds
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @computed_field
    @property
    def emails_enabled(self) -> bool:
        """Check if email configuration is complete."""
        return bool(
            self.SMTP_HOST
            and self.EMAILS_FROM_EMAIL
        )
    
    @computed_field
    @property
    def redis_enabled(self) -> bool:
        """Check if Redis is configured."""
        return bool(self.REDIS_URL)
    
    def get_db_url(self, is_test: bool = False) -> str:
        """Get the appropriate database URL."""
        return self.TEST_DATABASE_URL if is_test else self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    """
    Create cached settings instance.
    Use this function to get settings throughout the application.
    """
    return Settings()


# Create a singleton instance
settings = get_settings()