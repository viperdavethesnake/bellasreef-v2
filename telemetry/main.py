#!/usr/bin/env python3
"""
Telemetry Service - Main Application

This service provides a centralized API for querying historical data
from both raw history and hourly aggregates tables for any device.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from shared.core.config import settings
from shared.utils.logger import get_logger
from telemetry.api.history import router as history_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Telemetry Service...")
    logger.info(f"Service will run on {settings.SERVICE_HOST}:{settings.SERVICE_PORT_TELEMETRY}")
    yield
    logger.info("Shutting down Telemetry Service...")


# Create FastAPI application
app = FastAPI(
    title="Bella's Reef - Telemetry Service",
    description="Centralized API for querying historical data from all devices",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Bella's Reef Telemetry Service",
        "version": "1.0.0",
        "description": "Centralized API for historical data queries",
        "endpoints": {
            "docs": "/docs",
            "history": "/history/{device_id}/raw",
            "hourly": "/history/{device_id}/hourly"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "telemetry",
        "timestamp": "2025-06-22T20:00:00Z"
    }


# Include API routers
app.include_router(history_router, prefix="/api")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "telemetry.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT_TELEMETRY,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 