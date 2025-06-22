"""
SmartOutlet Exceptions

This module defines custom exceptions used by the smartoutlets module for error handling
across drivers, manager, and API layers.
"""


class SmartOutletError(Exception):
    """
    Base exception for smartoutlet operations.

    Attributes:
        message (str): Error message
        code (str): Error code for structured output
    """
    
    def __init__(self, message: str, code: str = "smart_outlet_error"):
        super().__init__(message)
        self.message = message
        self.code = code


class OutletNotFoundError(SmartOutletError):
    """
    Raised when a requested outlet is not found in the database.
    """
    
    def __init__(self, message: str):
        super().__init__(message, code="outlet_not_found")


class DriverNotImplementedError(SmartOutletError):
    """
    Raised when a driver type is not supported or disabled.
    """
    
    def __init__(self, message: str):
        super().__init__(message, code="driver_not_implemented")


class OutletConnectionError(SmartOutletError):
    """
    Raised when there's an error connecting to a smart outlet device.
    """
    
    def __init__(self, message: str):
        super().__init__(message, code="outlet_connection_error")


class OutletTimeoutError(OutletConnectionError):
    """
    Raised when a connection to a smart outlet device times out.
    """
    
    def __init__(self, message: str):
        super().__init__(message, code="outlet_timeout")


class OutletAuthenticationError(SmartOutletError):
    """
    Raised when authentication fails for a smart outlet device.
    """
    
    def __init__(self, message: str):
        super().__init__(message, code="outlet_authentication_error")


class OutletDisabledError(SmartOutletError):
    """
    Raised when an operation is attempted on a disabled outlet.
    """
    def __init__(self, message: str = "The operation cannot be completed because the outlet is disabled."):
        super().__init__(message, code="outlet_disabled")


class DiscoveryInProgressError(SmartOutletError):
    """
    Raised when a discovery task is already in progress.
    """
    def __init__(self, message: str = "A discovery task is already in progress."):
        super().__init__(message, code="discovery_in_progress")


class DiscoveryFailedError(SmartOutletError):
    """
    Raised when a discovery task fails.
    """
    def __init__(self, message: str):
        super().__init__(message, code="discovery_failed") 