"""
SmartOutlet Exception Handlers

This module provides FastAPI exception handlers for SmartOutlet errors,
mapping them to appropriate HTTP status codes with consistent response structures.
"""

from typing import Dict, Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .exceptions import (
    SmartOutletError,
    OutletNotFoundError,
    OutletConnectionError,
    OutletTimeoutError,
    OutletAuthenticationError,
    DriverNotImplementedError
)


def create_error_response(error: SmartOutletError) -> Dict[str, Any]:
    """
    Create a consistent error response structure.
    
    Args:
        error: The SmartOutlet error instance
        
    Returns:
        Dict containing the structured error response
    """
    return {
        "detail": {
            "code": error.code,
            "message": error.message
        }
    }


async def outlet_not_found_handler(request: Request, exc: OutletNotFoundError) -> JSONResponse:
    """Handle OutletNotFoundError - return 404 Not Found."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_response(exc)
    )


async def outlet_connection_handler(request: Request, exc: OutletConnectionError) -> JSONResponse:
    """Handle OutletConnectionError - return 503 Service Unavailable."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=create_error_response(exc)
    )


async def outlet_timeout_handler(request: Request, exc: OutletTimeoutError) -> JSONResponse:
    """Handle OutletTimeoutError - return 504 Gateway Timeout."""
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content=create_error_response(exc)
    )


async def outlet_authentication_handler(request: Request, exc: OutletAuthenticationError) -> JSONResponse:
    """Handle OutletAuthenticationError - return 401 Unauthorized."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=create_error_response(exc)
    )


async def driver_not_implemented_handler(request: Request, exc: DriverNotImplementedError) -> JSONResponse:
    """Handle DriverNotImplementedError - return 501 Not Implemented."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=create_error_response(exc)
    )


async def generic_smart_outlet_handler(request: Request, exc: SmartOutletError) -> JSONResponse:
    """Handle generic SmartOutletError - return 500 Internal Server Error."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(exc)
    )


def register_exception_handlers(app):
    """
    Register all SmartOutlet exception handlers with the FastAPI app.
    
    Args:
        app: The FastAPI application instance
    """
    app.add_exception_handler(OutletNotFoundError, outlet_not_found_handler)
    app.add_exception_handler(OutletConnectionError, outlet_connection_handler)
    app.add_exception_handler(OutletTimeoutError, outlet_timeout_handler)
    app.add_exception_handler(OutletAuthenticationError, outlet_authentication_handler)
    app.add_exception_handler(DriverNotImplementedError, driver_not_implemented_handler)
    app.add_exception_handler(SmartOutletError, generic_smart_outlet_handler) 