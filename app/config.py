from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/studyflow"

    # Clerk Auth
    CLERK_JWT_ISSUER: str
    CLERK_JWT_PUBLIC_KEY_URL: str

    # OpenAI API
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"

    # Server
    PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
