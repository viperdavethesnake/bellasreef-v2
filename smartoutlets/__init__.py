"""
SmartOutlets Module

This module provides smart outlet management capabilities for Bella's Reef.
"""

from .manager import SmartOutletManager
from shared.db.models import SmartOutlet, SmartOutletState
from .schemas import SmartOutletCreate, SmartOutletRead, SmartOutletUpdate
from .enums import OutletRole, SmartOutletDriverType
from .exceptions import (
    SmartOutletError,
    OutletNotFoundError,
    DriverNotImplementedError,
    OutletConnectionError,
    OutletTimeoutError,
    OutletAuthenticationError
)

__all__ = [
    "SmartOutletManager",
    "SmartOutlet",
    "SmartOutletState",
    "SmartOutletCreate",
    "SmartOutletRead", 
    "SmartOutletUpdate",
    "OutletRole",
    "SmartOutletDriverType",
    "SmartOutletError",
    "OutletNotFoundError",
    "DriverNotImplementedError",
    "OutletConnectionError",
    "OutletTimeoutError",
    "OutletAuthenticationError"
] 