"""
SmartOutlets Configuration Module

This module handles configuration for the smartoutlets module using pydantic-settings.
It provides environment-based settings and driver enablement logic.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class SmartOutletsSettings(BaseSettings):
    """
    Configuration settings for the SmartOutlets module.
    
    Uses pydantic-settings for environment variable loading with validation.
    """
    
    # Module enable/disable flags
    SMART_OUTLETS_ENABLED: bool = Field(default=True, description="Enable the SmartOutlets module")
    SMART_OUTLETS_KASA_ENABLED: bool = Field(default=True, description="Enable Kasa driver support")
    SMART_OUTLETS_SHELLY_ENABLED: bool = Field(default=True, description="Enable Shelly driver support")
    SMART_OUTLETS_VESYNC_ENABLED: bool = Field(default=True, description="Enable VeSync driver support")
    
    # VeSync cloud authentication
    VESYNC_EMAIL: Optional[str] = Field(default=None, description="VeSync account email")
    VESYNC_PASSWORD: Optional[str] = Field(default=None, description="VeSync account password")
    
    # Network and retry configuration
    OUTLET_TIMEOUT_SECONDS: int = Field(default=5, description="Timeout for outlet operations in seconds")
    OUTLET_MAX_RETRIES: int = Field(default=3, description="Maximum retry attempts for outlet operations")
    
    # Security
    ENCRYPTION_KEY: str = Field(description="Encryption key for sensitive data")
    SMART_OUTLETS_API_KEY: str = Field(description="API key for SmartOutlets authentication")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = SmartOutletsSettings()


def is_driver_enabled(driver_type: str) -> bool:
    """
    Return whether the given driver is enabled via config.
    
    Args:
        driver_type (str): The driver type to check. Must be one of: "kasa", "shelly", "vesync"
        
    Returns:
        bool: True if the driver is enabled, False otherwise
        
    Raises:
        ValueError: If driver_type is not a supported value
    """
    if not settings.SMART_OUTLETS_ENABLED:
        return False
    
    driver_type = driver_type.lower()
    
    if driver_type == "kasa":
        return settings.SMART_OUTLETS_KASA_ENABLED
    elif driver_type == "shelly":
        return settings.SMART_OUTLETS_SHELLY_ENABLED
    elif driver_type == "vesync":
        return settings.SMART_OUTLETS_VESYNC_ENABLED
    else:
        raise ValueError(f"Unsupported driver type: {driver_type}. Must be one of: kasa, shelly, vesync")


__all__ = [
    "SmartOutletsSettings",
    "settings",
    "is_driver_enabled"
] 