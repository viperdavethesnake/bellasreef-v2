import os
from typing import Union, List
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from temp/.env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

class TempSettings(BaseSettings):
    """
    Bella's Reef Temperature Service settings.
    
    This settings model loads from /temp/.env and includes
    all configuration needed for temperature probe management.
    """
    
    # =============================================================================
    # SERVICE ENABLEMENT (CRITICAL)
    # =============================================================================
    
    # Enable/disable the temperature service
    TEMP_ENABLED: bool = True
    
    # =============================================================================
    # REQUIRED SECURITY SETTINGS
    # =============================================================================
    
    # Service Authentication Token
    SERVICE_TOKEN: str
    
    # Database Configuration
    DATABASE_URL: str
    
    # =============================================================================
    # SERVICE CONFIGURATION
    # =============================================================================
    
    SERVICE_PORT: int = 8004
    SERVICE_HOST: str = "0.0.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # =============================================================================
    # HARDWARE CONFIGURATION
    # =============================================================================
    
    W1_GPIO_PIN: int = 4
    W1_DEVICE_DIR: str = "/sys/bus/w1/devices"
    
    # =============================================================================
    # API CONFIGURATION
    # =============================================================================
    
    ALLOWED_HOSTS: Union[str, List[str]] = "*"
    
    # =============================================================================
    # FIELD VALIDATORS
    # =============================================================================
    
    @field_validator("TEMP_ENABLED")
    @classmethod
    def validate_temp_enabled(cls, v: Union[str, bool]) -> bool:
        """Validate TEMP_ENABLED is a boolean."""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
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
    
    @field_validator("W1_GPIO_PIN")
    @classmethod
    def validate_w1_gpio_pin(cls, v: Union[str, int]) -> int:
        """Validate 1-wire GPIO pin number."""
        try:
            pin = int(v)
            if not (1 <= pin <= 40):
                raise ValueError("W1_GPIO_PIN must be between 1 and 40")
            return pin
        except (ValueError, TypeError):
            raise ValueError(f"Invalid W1_GPIO_PIN: {v}")
    
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
            import json
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
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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