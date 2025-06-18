from pathlib import Path
from typing import List, Optional, Literal
from pydantic import field_validator, PostgresDsn
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Bella's Reef"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENV: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "bellasreef"
    DATABASE_URL: Optional[PostgresDsn] = None

    # Hardware
    PWM_FREQUENCY: int = 1000
    PWM_CHANNELS: int = 16
    SENSOR_POLL_INTERVAL: int = 60  # seconds

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
    ]

    # Email (future alerting)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be set and at least 32 characters long.")
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v, info):
        if v:
            return v
        values = info.data
        return PostgresDsn.build(
            scheme="postgresql",
            user=values["POSTGRES_USER"],
            password=values["POSTGRES_PASSWORD"],
            host=values["POSTGRES_SERVER"],
            path=f"/{values['POSTGRES_DB']}",
        )

settings = Settings()
