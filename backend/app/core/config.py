"""
Application configuration using Pydantic Settings.
Supports environment variables with validation and type conversion.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_ENV: str = Field(default="local", description="Application environment")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/guideline_transform",
        description="Database connection URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Queue Configuration
    QUEUE_ADAPTER: str = Field(default="celery", description="Queue adapter: celery or sqs")
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL"
    )
    CELERY_WORKER_CONCURRENCY: int = Field(
        default=4,
        description="Celery worker concurrency"
    )
    
    # AWS/SQS Configuration (for production)
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="AWS access key")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, description="AWS secret key")
    AWS_SQS_QUEUE_URL: Optional[str] = Field(default=None, description="SQS queue URL")
    
    # S3/MinIO Storage
    S3_ENDPOINT_URL: str = Field(
        default="http://localhost:9000",
        description="S3 endpoint URL (MinIO or AWS)"
    )
    S3_ACCESS_KEY: str = Field(default="minioadmin", description="S3 access key")
    S3_SECRET_KEY: str = Field(default="minioadmin", description="S3 secret key")
    S3_BUCKET: str = Field(default="guideline-transform", description="S3 bucket name")
    S3_USE_SSL: bool = Field(default=False, description="Use SSL for S3 connections")
    
    # AI/LLM Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google AI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")
    DEFAULT_LLM_MODEL: str = Field(default="gpt-4o-mini", description="Default LLM model")
    DEFAULT_LLM_PROVIDER: str = Field(default="openai", description="Default LLM provider")

    # Azure Document Intelligence Configuration
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: Optional[str] = Field(
        default=None,
        description="Azure Document Intelligence API endpoint"
    )
    AZURE_DOCUMENT_INTELLIGENCE_KEY: Optional[str] = Field(
        default=None,
        description="Azure Document Intelligence API key"
    )
    
    # JWT/Auth Configuration
    JWT_SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="JWT secret key"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT access token expiration in minutes"
    )
    
    # File Processing Configuration
    MAX_FILE_SIZE_MB: int = Field(default=50, description="Maximum file size in MB")
    ALLOWED_FILE_EXTENSIONS: str = Field(
        default="pdf",
        description="Allowed file extensions (comma-separated)"
    )
    PDF_DPI: int = Field(default=300, description="PDF processing DPI")
    OCR_ENABLED: bool = Field(default=False, description="Enable OCR processing")
    
    # Worker Configuration
    DRAFT_RETRY_MAX_ATTEMPTS: int = Field(
        default=3,
        description="Maximum retry attempts for draft generation"
    )
    DRAFT_RETRY_BACKOFF_FACTOR: float = Field(
        default=2.0,
        description="Backoff factor for draft retries"
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=60,
        description="Rate limit requests per minute"
    )
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    PROMETHEUS_ENABLED: bool = Field(default=False, description="Enable Prometheus metrics")
    METRICS_PORT: int = Field(default=9090, description="Metrics server port")
    
    # CORS Configuration
    ALLOWED_HOSTS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @validator("QUEUE_ADAPTER")
    def validate_queue_adapter(cls, v):
        """Validate queue adapter."""
        valid_adapters = ["celery", "sqs"]
        if v.lower() not in valid_adapters:
            raise ValueError(f"QUEUE_ADAPTER must be one of {valid_adapters}")
        return v.lower()
    
    @validator("DEFAULT_LLM_PROVIDER")
    def validate_llm_provider(cls, v):
        """Validate LLM provider."""
        valid_providers = ["openai", "anthropic", "google"]
        if v.lower() not in valid_providers:
            raise ValueError(f"DEFAULT_LLM_PROVIDER must be one of {valid_providers}")
        return v.lower()
    
    @validator("ALLOWED_FILE_EXTENSIONS")
    def validate_file_extensions(cls, v):
        """Convert comma-separated extensions to list."""
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV.lower() in ["production", "prod"]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV.lower() in ["local", "development", "dev"]
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.DATABASE_URL.replace("+asyncpg", "")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 