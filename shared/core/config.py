import json
import re
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from core/.env
env_path = Path(__file__).parent.parent.parent / "core" / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class Settings(BaseSettings):
    """
    Bella's Reef Core Service settings with minimal, secure configuration.
    
    This settings model matches the core service environment structure:
    - Loads from /core/.env (not project root)
    - Only includes fields needed for core service (auth, health, users)
    - Comprehensive security validation
    - Clear error messages for deployment
    """
    
    # =============================================================================
    # REQUIRED SECURITY SETTINGS
    # =============================================================================
    
    # Service Authentication (inter-service API auth)
    SERVICE_TOKEN: str
    
    # Database Configuration (PostgreSQL connection string)
    DATABASE_URL: str
    
    # Security Settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS Settings (allowed origins for web requests)
    ALLOWED_HOSTS: Union[str, List[str]] = "*"
    
    # Service Configuration
    SERVICE_PORT: int = 8000
    SERVICE_HOST: str = "0.0.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Admin User (for database initialization)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "reefrocks"
    ADMIN_EMAIL: str = "admin@example.com"
    
    # =============================================================================
    # FIELD VALIDATORS
    # =============================================================================
    
    @field_validator("SERVICE_TOKEN")
    @classmethod
    def validate_service_token(cls, v: str) -> str:
        """Validate SERVICE_TOKEN - must not be default value."""
        if not v or v.strip() == "changeme_secure_token_here":
            raise ValueError(
                "SERVICE_TOKEN must be set to a secure value. "
                "Generate with: openssl rand -hex 32"
            )
        return v.strip()
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL format."""
        if not v or not v.strip():
            raise ValueError("DATABASE_URL is required")
        
        v = v.strip()
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must start with 'postgresql://'")
        
        return v
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate SECRET_KEY - must be secure and non-default."""
        if not v or len(v.strip()) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long. "
                "Generate with: openssl rand -hex 32"
            )
        
        # Check for default/unsafe values
        unsafe_keys = [
            "your_super_secret_key_here_change_this_in_production",
            "your-super-secret-key-change-this-in-production",
            "default-secret-key",
            "changeme"
        ]
        
        if v.strip() in unsafe_keys:
            raise ValueError(
                "SECRET_KEY must not use default/example values. "
                "Generate a secure random key for production."
            )
        
        return v.strip()
    
    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_token_expire(cls, v: Union[str, int]) -> int:
        """Validate token expiration time."""
        try:
            minutes = int(v)
            if not (1 <= minutes <= 10080):  # 1 minute to 1 week
                raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 10080")
            return minutes
        except (ValueError, TypeError):
            raise ValueError(f"Invalid ACCESS_TOKEN_EXPIRE_MINUTES: {v}")
    
    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse ALLOWED_HOSTS from various formats."""
        if isinstance(v, list):
            return v
        
        if not isinstance(v, str):
            raise ValueError("ALLOWED_HOSTS must be a string or list")
        
        v = v.strip()
        
        # Handle wildcard
        if v == "*":
            print("⚠️  WARNING: Using wildcard ALLOWED_HOSTS. Insecure for production!")
            return ["*"]
        
        # Try JSON parsing first
        try:
            hosts = json.loads(v)
            if isinstance(hosts, list):
                return hosts
            else:
                raise ValueError("ALLOWED_HOSTS JSON must be an array")
        except json.JSONDecodeError:
            pass
        
        # Fallback: comma-separated string
        hosts = [host.strip() for host in v.split(",") if host.strip()]
        
        # Validate individual hosts
        for host in hosts:
            if host == "*":
                print("⚠️  WARNING: Wildcard '*' found in ALLOWED_HOSTS. Insecure for production!")
            elif not (host.startswith("http://") or host.startswith("https://")):
                print(f"⚠️  WARNING: Host '{host}' may not be valid (should start with http:// or https://)")
        
        return hosts
    
    @field_validator("SERVICE_PORT")
    @classmethod
    def validate_service_port(cls, v: Union[str, int]) -> int:
        """Validate service port number."""
        try:
            port = int(v)
            if not (1 <= port <= 65535):
                raise ValueError("SERVICE_PORT must be between 1 and 65535")
            return port
        except (ValueError, TypeError):
            raise ValueError(f"Invalid SERVICE_PORT: {v}")
    
    @field_validator("ADMIN_PASSWORD")
    @classmethod
    def validate_admin_password(cls, v: str) -> str:
        """Validate admin password security."""
        if not v or len(v.strip()) < 8:
            raise ValueError("ADMIN_PASSWORD must be at least 8 characters long")
        
        # Warn about weak passwords
        weak_passwords = ["reefrocks", "admin", "password", "123456", "admin123"]
        if v.lower() in weak_passwords:
            print("⚠️  WARNING: Using weak admin password. Change for production!")
        
        return v.strip()
    
    @field_validator("ADMIN_EMAIL")
    @classmethod
    def validate_admin_email(cls, v: str) -> str:
        """Validate admin email format."""
        if not v or "@" not in v or "." not in v:
            raise ValueError("ADMIN_EMAIL must be a valid email address")
        
        # Warn about example emails
        if "example.com" in v or "test.com" in v:
            print("⚠️  WARNING: Using example email address. Update for production!")
        
        return v.strip()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._print_security_warnings()
    
    def _print_security_warnings(self):
        """Print security warnings for risky configurations."""
        warnings = []
        
        if "*" in self.ALLOWED_HOSTS:
            warnings.append("Wildcard ALLOWED_HOSTS in use")
        
        if self.ADMIN_PASSWORD.lower() in ["reefrocks", "admin", "password"]:
            warnings.append("Using weak admin password")
        
        if "example.com" in self.ADMIN_EMAIL:
            warnings.append("Using example email address")
        
        if warnings:
            print("\n🔒 SECURITY WARNINGS:")
            for warning in warnings:
                print(f"   ⚠️  {warning}")
            print("   Please review and update these settings for production.\n")

# Create settings instance
settings = Settings()
