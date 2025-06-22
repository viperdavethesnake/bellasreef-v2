"""
Bella's Reef - Unified Configuration Settings

This module provides a single, unified configuration for all services
in the Bella's Reef project. It loads settings from a single .env file
at the project root.
"""

import json
from typing import List, Union
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Unified settings for all services. Loads from a single .env file
    at the project root using Pydantic's ConfigDict for cleaner setup.
    """
    model_config = ConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    # =============================================================================
    # REQUIRED SECURITY & DATABASE SETTINGS (SHARED)
    # =============================================================================
    SERVICE_TOKEN: str
    DATABASE_URL: str
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # =============================================================================
    # CORE & WEB SETTINGS
    # =============================================================================
    CORE_ENABLED: bool = True
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "your_secure_password"
    ADMIN_EMAIL: str = "admin@example.com"
    ALLOWED_HOSTS: Union[str, List[str]] = "*"
    SERVICE_PORT_CORE: int = 8000

    # =============================================================================
    # GENERAL SERVICE SETTINGS
    # =============================================================================
    SERVICE_HOST: str = "0.0.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # =============================================================================
    # CONTROL SERVICE (HARDWARE) SETTINGS
    # =============================================================================
    RPI_PLATFORM: str = "none"
    PWM_GPIO_PINS: str = ""
    PWM_FREQUENCY: int = 1000
    PWM_CHANNELS: int = 16
    PCA9685_ENABLED: bool = False
    PCA9685_ADDRESS: str = "0x40"
    PCA9685_FREQUENCY: int = 1000

    # =============================================================================
    # TEMPERATURE SERVICE SETTINGS
    # =============================================================================
    TEMP_ENABLED: bool = True
    SERVICE_PORT_TEMP: int = 8004
    SENSOR_POLL_INTERVAL: int = 30
    W1_GPIO_PIN: int = 4

    # =============================================================================
    # SMARTOUTLETS SERVICE SETTINGS
    # =============================================================================
    SMART_OUTLETS_ENABLED: bool = True
    SERVICE_PORT_SMARTOUTLETS: int = 8005
    SMART_OUTLETS_KASA_ENABLED: bool = True
    SMART_OUTLETS_SHELLY_ENABLED: bool = True
    SMART_OUTLETS_VESYNC_ENABLED: bool = True
    VESYNC_EMAIL: str = ""
    VESYNC_PASSWORD: str = ""
    OUTLET_TIMEOUT_SECONDS: int = 5
    OUTLET_MAX_RETRIES: int = 3

    # =============================================================================
    # FIELD VALIDATORS
    # =============================================================================
    @field_validator("SERVICE_TOKEN", "SECRET_KEY", "ENCRYPTION_KEY")
    @classmethod
    def validate_security_keys(cls, v: str, info) -> str:
        """Validate that security keys are not empty or default."""
        if not v or "changeme" in v or "your_super_secret_key" in v:
            raise ValueError(
                f"{info.field_name} must be set to a secure, non-default value. "
                "Generate one with: openssl rand -hex 32"
            )
        return v.strip()

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL format."""
        if not v or not v.strip().startswith("postgresql://"):
            raise ValueError("DATABASE_URL is required and must start with 'postgresql://'")
        return v.strip()

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse ALLOWED_HOSTS from a comma-separated string or JSON array."""
        if isinstance(v, list):
            return v
        if not isinstance(v, str):
            raise ValueError("ALLOWED_HOSTS must be a string or list")
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format for ALLOWED_HOSTS")
        return [host.strip() for host in v.split(",") if host.strip()]

    # =============================================================================
    # COMPUTED PROPERTIES
    # =============================================================================
    @property
    def PWM_GPIO_PIN_LIST(self) -> List[int]:
        """Convert PWM_GPIO_PINS string to a list of integers."""
        if not self.PWM_GPIO_PINS:
            return []
        try:
            return [int(pin.strip()) for pin in self.PWM_GPIO_PINS.split(",") if pin.strip()]
        except ValueError:
            raise ValueError("PWM_GPIO_PINS must be a comma-separated list of numbers.")

settings = Settings()

def is_driver_enabled(driver_type: str) -> bool:
    """
    Check if a specific smart outlet driver type is enabled.
    
    Args:
        driver_type: The driver type to check (kasa, shelly, vesync)
        
    Returns:
        bool: True if the driver type is enabled
    """
    driver_enabled_map = {
        "kasa": settings.SMART_OUTLETS_KASA_ENABLED,
        "shelly": settings.SMART_OUTLETS_SHELLY_ENABLED,
        "vesync": settings.SMART_OUTLETS_VESYNC_ENABLED,
    }
    
    return driver_enabled_map.get(driver_type.lower(), False)
