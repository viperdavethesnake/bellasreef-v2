"""
Bella's Reef - Temperature Service Configuration
Self-contained configuration that only reads from temp/.env
"""

import os
from pathlib import Path
from typing import List, Union
import json
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

class TempSettings(BaseSettings):
    """
    Temperature Service settings with self-contained configuration.
    
    This settings model only reads from temp/.env and is completely
    independent of other services.
    """
    
    # =============================================================================
    # REQUIRED SETTINGS
    # =============================================================================
    
    # Service Authentication
    SERVICE_TOKEN: str = Field(..., description="Service authentication token")
    
    # Database Configuration
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    
    # Service Configuration
    SERVICE_HOST: str = Field(default="0.0.0.0", description="Service host")
    SERVICE_PORT: int = Field(default=8004, description="Service port")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    
    # CORS Settings
    ALLOWED_HOSTS: Union[str, List[str]] = Field(default="*", description="Allowed CORS origins")
    
    # Temperature Service Settings
    TEMP_ENABLED: bool = Field(default=True, description="Enable temperature service")
    SENSOR_POLL_INTERVAL: int = Field(default=30, description="Sensor polling interval in seconds")
    W1_GPIO_PIN: int = Field(default=4, description="GPIO pin for 1-wire data line")
    
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
    
    def __init__(self, **kwargs):
        # Set the env file path to temp/.env
        env_file = Path(__file__).parent / ".env"
        super().__init__(_env_file=env_file, **kwargs)
        self._print_security_warnings()
    
    def _print_security_warnings(self):
        """Print security warnings for risky configurations."""
        warnings = []
        
        if "*" in self.ALLOWED_HOSTS:
            warnings.append("Wildcard ALLOWED_HOSTS in use")
        
        if warnings:
            print("\n🔒 SECURITY WARNINGS:")
            for warning in warnings:
                print(f"   ⚠️  {warning}")
            print("   Please review and update these settings for production.\n")

# Create settings instance
settings = TempSettings() 