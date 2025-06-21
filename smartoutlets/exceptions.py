"""
SmartOutlet Exceptions

This module defines custom exceptions used by the smartoutlets module.
"""


class SmartOutletError(Exception):
    """Base exception for smartoutlet operations."""
    
    def __init__(self, message: str, code: str = "smart_outlet_error"):
        super().__init__(message)
        self.message = message
        self.code = code


class OutletNotFoundError(SmartOutletError):
    """Raised when a requested outlet is not found in the database."""
    
    def __init__(self, message: str):
        super().__init__(message, code="outlet_not_found")


class DriverNotImplementedError(SmartOutletError):
    """Raised when a driver type is not supported or disabled."""
    
    def __init__(self, message: str):
        super().__init__(message, code="driver_not_implemented")


class OutletConnectionError(SmartOutletError):
    """Raised when there's an error connecting to a smart outlet device."""
    
    def __init__(self, message: str):
        super().__init__(message, code="outlet_connection_error")


class OutletTimeoutError(OutletConnectionError):
    """Raised when a connection to a smart outlet device times out."""
    
    def __init__(self, message: str):
        super().__init__(message, code="outlet_timeout")


class OutletAuthenticationError(SmartOutletError):
    """Raised when authentication fails for a smart outlet device."""
    
    def __init__(self, message: str):
        super().__init__(message, code="outlet_authentication_error") 