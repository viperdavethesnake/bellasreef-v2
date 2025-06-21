"""
SmartOutlet Exceptions

This module defines custom exceptions used by the smartoutlets module.
"""


class SmartOutletError(Exception):
    """Base exception for smartoutlet operations."""
    pass


class OutletNotFoundError(SmartOutletError):
    """Raised when a requested outlet is not found in the database."""
    pass


class DriverNotImplementedError(SmartOutletError):
    """Raised when a driver type is not supported or disabled."""
    pass


class OutletConnectionError(SmartOutletError):
    """Raised when there's an error connecting to a smart outlet device."""
    pass


class OutletTimeoutError(OutletConnectionError):
    """Raised when a connection to a smart outlet device times out."""
    pass


class OutletAuthenticationError(SmartOutletError):
    """Raised when authentication fails for a smart outlet device."""
    pass 