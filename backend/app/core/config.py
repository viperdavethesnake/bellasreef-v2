from pathlib import Path
from typing import Optional
import os
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Bella's Reef"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV == "development"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "bellasreef")
    DATABASE_URL: Optional[PostgresDsn] = None
    
    # Hardware
    PWM_FREQUENCY: int = int(os.getenv("PWM_FREQUENCY", "1000"))  # Hz
    PWM_CHANNELS: int = int(os.getenv("PWM_CHANNELS", "16"))
    SENSOR_POLL_INTERVAL: int = int(os.getenv("SENSOR_POLL_INTERVAL", "60"))  # seconds
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
    ]
    
    # Email (for future alerting)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, any]) -> any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        if not v:
            raise ValueError("SECRET_KEY must be set")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("POSTGRES_PASSWORD")
    def validate_postgres_password(cls, v: str) -> str:
        if not v:
            raise ValueError("POSTGRES_PASSWORD must be set")
        return v
    
    @validator("ENV")
    def validate_env(cls, v: str) -> str:
        allowed = ["development", "testing", "production"]
        if v not in allowed:
            raise ValueError(f"ENV must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    class Config:
        case_sensitive = True
        env_file = env_path

# Create global settings instance
settings = Settings() 