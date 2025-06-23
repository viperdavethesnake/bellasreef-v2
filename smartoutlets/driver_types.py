"""
SmartOutlet Driver Types

This module defines driver types used by the smartoutlets module.
"""

from enum import Enum


class SmartOutletDriverType(str, Enum):
    """Supported smart outlet driver types."""
    KASA = "kasa"
    SHELLY = "shelly"
    VESYNC = "vesync" 