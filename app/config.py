"""
Configuration settings for StudyFlow backend.
"""

from pydantic_settings import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://studyflow:studyflow_password@localhost:5432/studyflow",
        description="PostgreSQL database connection string",
    )

    # GLM-4.7 API (Zhipu AI)
    GLM_API_KEY: str = Field(
        default="",
        description="GLM-4.7 API key from Zhipu AI",
    )

    # CORS
    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for CORS",
    )

    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Application environment (development/production)",
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="info",
        description="Logging level (debug/info/warning/error)",
    )

    # Server
    PORT: int = Field(
        default=8000,
        description="Server port",
    )

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
