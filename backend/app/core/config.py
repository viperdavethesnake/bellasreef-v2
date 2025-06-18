from pathlib import Path
from typing import List, Optional, Literal
from pydantic import field_validator, computed_field
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
    POSTGRES_PORT: Optional[int] = 5432

    # Admin User (for database initialization)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "reefrocks"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PHONE: str = "+15555555555"

    # Hardware
    PWM_FREQUENCY: int = 1000
    PWM_CHANNELS: int = 16
    SENSOR_POLL_INTERVAL: int = 60  # seconds
    
    # Raspberry Pi Platform
    RPI_PLATFORM: Literal["auto", "legacy", "rpi5", "none"] = "auto"
    
    # PCA9685 Configuration
    PCA9685_ADDRESS: str = "0x40"
    PCA9685_FREQUENCY: int = 1000

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

    @computed_field
    def DATABASE_URL(self) -> str:
        """Assemble database URL from individual components."""
        if self.POSTGRES_PORT and self.POSTGRES_PORT != 5432:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        else:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

settings = Settings()
