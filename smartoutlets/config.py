"""
SmartOutlets Configuration Module

This module handles enable/disable flags for the smartoutlets module and each supported driver.
It also loads cloud auth for VeSync from environment variables.
"""

import os


def _parse_bool(value: str, default: bool = False) -> bool:
    """
    Parse a string value to boolean with comprehensive support.
    
    Args:
        value: The string value to parse
        default: Default value if parsing fails
        
    Returns:
        bool: Parsed boolean value or default
    """
    if not value:
        return default
    
    value_lower = value.lower().strip()
    
    # True values
    if value_lower in ('true', '1', 'yes', 'on'):
        return True
    
    # False values
    if value_lower in ('false', '0', 'no', 'off'):
        return False
    
    # Invalid value - return default
    return default


# Module enable/disable flags
SMART_OUTLETS_ENABLED = _parse_bool(
    os.getenv('SMART_OUTLETS_ENABLED', 'true'), 
    default=True
)

# Driver-specific enable/disable flags
SMART_OUTLETS_KASA_ENABLED = _parse_bool(
    os.getenv('SMART_OUTLETS_KASA_ENABLED', 'true'), 
    default=True
)

SMART_OUTLETS_SHELLY_ENABLED = _parse_bool(
    os.getenv('SMART_OUTLETS_SHELLY_ENABLED', 'true'), 
    default=True
)

SMART_OUTLETS_VESYNC_ENABLED = _parse_bool(
    os.getenv('SMART_OUTLETS_VESYNC_ENABLED', 'true'), 
    default=True
)

# VeSync cloud authentication
VESYNC_EMAIL = os.getenv('VESYNC_EMAIL', 'user@example.com')
VESYNC_PASSWORD = os.getenv('VESYNC_PASSWORD', 'your_password')


def is_driver_enabled(driver_type: str) -> bool:
    """
    Return whether the given driver is enabled via config.
    
    Args:
        driver_type: The driver type to check. Must be one of: "kasa", "shelly", "vesync"
        
    Returns:
        bool: True if the driver is enabled, False otherwise
        
    Raises:
        ValueError: If driver_type is not a supported value
    """
    if not SMART_OUTLETS_ENABLED:
        return False
    
    driver_type = driver_type.lower()
    
    if driver_type == "kasa":
        return SMART_OUTLETS_KASA_ENABLED
    elif driver_type == "shelly":
        return SMART_OUTLETS_SHELLY_ENABLED
    elif driver_type == "vesync":
        return SMART_OUTLETS_VESYNC_ENABLED
    else:
        raise ValueError(f"Unsupported driver type: {driver_type}. Must be one of: kasa, shelly, vesync")


__all__ = [
    "SMART_OUTLETS_ENABLED",
    "SMART_OUTLETS_KASA_ENABLED",
    "SMART_OUTLETS_SHELLY_ENABLED",
    "SMART_OUTLETS_VESYNC_ENABLED",
    "VESYNC_EMAIL",
    "VESYNC_PASSWORD",
    "is_driver_enabled"
] 