import json
import re
import secrets
from pathlib import Path
from typing import List, Optional, Literal, Union
from pydantic import field_validator, computed_field, ValidationError
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class Settings(BaseSettings):
    """
    Bella's Reef application settings with comprehensive validation.
    
    Features:
    - Robust parsing of environment variables (JSON, strings, legacy formats)
    - Security warnings for risky configurations
    - Comprehensive validation with helpful error messages
    - Pydantic v2 compatibility with computed fields
    """
    
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

    # CORS - Loaded as JSON string from environment
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

    # =============================================================================
    # Field Validators
    # =============================================================================

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate SECRET_KEY for security requirements."""
        if not v or len(v.strip()) < 32:
            raise ValueError(
                "SECRET_KEY must be set and at least 32 characters long. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        # Warn about weak secret keys
        if v in ["your-super-secret-key-change-this-in-production-minimum-32-chars", 
                 "change-this-in-production", "default-secret-key"]:
            print("⚠️  WARNING: Using default SECRET_KEY. Change this in production!")
        
        return v.strip()

    @field_validator("ADMIN_PASSWORD")
    @classmethod
    def validate_admin_password(cls, v: str) -> str:
        """Validate admin password for security."""
        if not v or len(v.strip()) < 8:
            raise ValueError("ADMIN_PASSWORD must be at least 8 characters long.")
        
        # Warn about weak passwords
        weak_passwords = ["reefrocks", "admin", "password", "123456", "admin123"]
        if v.lower() in weak_passwords:
            print("⚠️  WARNING: Using weak admin password. Change this in production!")
        
        return v.strip()

    @field_validator("ADMIN_EMAIL")
    @classmethod
    def validate_admin_email(cls, v: str) -> str:
        """Validate admin email format."""
        if not v or "@" not in v or "." not in v:
            raise ValueError("ADMIN_EMAIL must be a valid email address.")
        
        # Warn about example emails
        if "example.com" in v or "test.com" in v:
            print("⚠️  WARNING: Using example email address. Update for production!")
        
        return v.strip()

    @field_validator("POSTGRES_PORT")
    @classmethod
    def validate_postgres_port(cls, v: Union[str, int, None]) -> Optional[int]:
        """Parse and validate PostgreSQL port."""
        if v is None:
            return 5432
        
        try:
            port = int(v)
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535")
            return port
        except (ValueError, TypeError):
            raise ValueError(f"Invalid port number: {v}. Must be an integer between 1-65535.")

    @field_validator("PWM_FREQUENCY")
    @classmethod
    def validate_pwm_frequency(cls, v: Union[str, int]) -> int:
        """Parse and validate PWM frequency."""
        try:
            freq = int(v)
            if not (1 <= freq <= 1000000):  # 1Hz to 1MHz
                raise ValueError("PWM frequency must be between 1Hz and 1MHz")
            return freq
        except (ValueError, TypeError):
            raise ValueError(f"Invalid PWM frequency: {v}. Must be an integer between 1-1000000.")

    @field_validator("PWM_CHANNELS")
    @classmethod
    def validate_pwm_channels(cls, v: Union[str, int]) -> int:
        """Parse and validate PWM channels count."""
        try:
            channels = int(v)
            if not (1 <= channels <= 64):  # Reasonable range for PWM controllers
                raise ValueError("PWM channels must be between 1 and 64")
            return channels
        except (ValueError, TypeError):
            raise ValueError(f"Invalid PWM channels: {v}. Must be an integer between 1-64.")

    @field_validator("PCA9685_ADDRESS")
    @classmethod
    def validate_pca9685_address(cls, v: str) -> str:
        """Parse and validate PCA9685 I2C address."""
        v = v.strip().lower()
        
        # Handle different address formats
        if v.startswith("0x"):
            try:
                addr = int(v, 16)
            except ValueError:
                raise ValueError(f"Invalid hex address: {v}")
        else:
            try:
                addr = int(v)
            except ValueError:
                raise ValueError(f"Invalid address: {v}")
        
        # PCA9685 valid addresses: 0x40-0x7F (64-127)
        if not (0x40 <= addr <= 0x7F):
            raise ValueError(f"PCA9685 address must be between 0x40-0x7F (64-127), got: {v}")
        
        return f"0x{addr:02x}"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Parse CORS_ORIGINS from various formats with security warnings.
        
        Supports:
        - JSON array: '["http://localhost", "https://example.com"]'
        - Comma-separated: 'http://localhost,https://example.com'
        - Single origin: 'http://localhost'
        - Wildcard: '*' or '["*"]' (with warning)
        - Empty string: '' (converts to wildcard with warning)
        """
        if isinstance(v, list):
            return v
        
        if not isinstance(v, str):
            raise ValueError(f"CORS_ORIGINS must be a string or list, got: {type(v)}")
        
        v = v.strip()
        
        # Handle empty string
        if v == "":
            print("⚠️  WARNING: Empty CORS_ORIGINS converted to wildcard ['*']")
            return ["*"]
        
        # Handle wildcard
        if v == "*" or v == '["*"]':
            print("⚠️  WARNING: Using wildcard CORS_ORIGINS. This is insecure for production!")
            return ["*"]
        
        # Try JSON parsing first
        try:
            origins = json.loads(v)
            if isinstance(origins, list):
                # Check for wildcard in JSON array
                if "*" in origins:
                    print("⚠️  WARNING: Wildcard '*' found in CORS_ORIGINS. Insecure for production!")
                return origins
            else:
                raise ValueError("CORS_ORIGINS JSON must be an array")
        except json.JSONDecodeError:
            pass
        
        # Fallback: comma-separated string
        origins = [origin.strip() for origin in v.split(",") if origin.strip()]
        
        # Validate individual origins
        for origin in origins:
            if origin == "*":
                print("⚠️  WARNING: Wildcard '*' found in CORS_ORIGINS. Insecure for production!")
            elif not (origin.startswith("http://") or origin.startswith("https://")):
                print(f"⚠️  WARNING: CORS origin '{origin}' may not be valid (should start with http:// or https://)")
        
        return origins

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level = v.upper().strip()
        
        if level not in valid_levels:
            raise ValueError(f"Invalid LOG_LEVEL: {v}. Must be one of: {', '.join(valid_levels)}")
        
        return level

    @field_validator("SENSOR_POLL_INTERVAL")
    @classmethod
    def validate_sensor_poll_interval(cls, v: Union[str, int]) -> int:
        """Parse and validate sensor polling interval."""
        try:
            interval = int(v)
            if not (1 <= interval <= 3600):  # 1 second to 1 hour
                raise ValueError("Sensor poll interval must be between 1 and 3600 seconds")
            return interval
        except (ValueError, TypeError):
            raise ValueError(f"Invalid sensor poll interval: {v}. Must be an integer between 1-3600.")

    @computed_field
    def DATABASE_URL(self) -> str:
        """Assemble database URL from individual components."""
        if self.POSTGRES_PORT and self.POSTGRES_PORT != 5432:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        else:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._print_security_warnings()

    def _print_security_warnings(self):
        """Print security warnings for risky configurations."""
        warnings = []
        
        if self.ENV == "production" and self.DEBUG:
            warnings.append("DEBUG=True in production environment")
        
        if self.ENV == "production" and "*" in self.CORS_ORIGINS:
            warnings.append("Wildcard CORS_ORIGINS in production")
        
        if self.ADMIN_PASSWORD == "reefrocks":
            warnings.append("Using default admin password")
        
        if self.SECRET_KEY in ["your-super-secret-key-change-this-in-production-minimum-32-chars"]:
            warnings.append("Using default SECRET_KEY")
        
        if warnings:
            print("\n🔒 SECURITY WARNINGS:")
            for warning in warnings:
                print(f"   ⚠️  {warning}")
            print("   Please review and update these settings for production.\n")

settings = Settings()
