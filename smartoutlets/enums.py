"""
SmartOutlet Enums

This module defines enums used by the smartoutlets module.
"""

from enum import Enum


class OutletRole(str, Enum):
    """Roles that smart outlets can serve in the aquarium system."""
    LIGHT = "light"
    HEATER = "heater"
    CHILLER = "chiller"
    PUMP = "pump"
    WAVEMAKER = "wavemaker"
    SKIMMER = "skimmer"
    FEEDER = "feeder"
    UV = "uv"
    OZONE = "ozone"
    OTHER = "other"


class SmartOutletDriverType(str, Enum):
    """Supported smart outlet driver types."""
    KASA = "kasa"
    SHELLY = "shelly"
    VESYNC = "vesync" 