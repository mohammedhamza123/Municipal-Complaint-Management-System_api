"""
Configuration settings for the application
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Union


class Settings(BaseSettings):
    """Application settings"""

    # Database
    DATABASE_URL: str = "sqlite:///./municipal_complaints.db"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Application
    APP_NAME: str = "Smart Municipal Complaint Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 2

    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = "firebase-service-account.json"

    # CORS — comma-separated origins or *
    CORS_ORIGINS: Union[str, list[str]] = "*"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if value is None or value == "":
            return ["*"]
        if isinstance(value, str):
            if value.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()




