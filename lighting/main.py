"""
Main FastAPI application for the Lighting API Service.

This module provides the main FastAPI application that serves the lighting system API,
including all behavior management, runner control, effects, and scheduler endpoints.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

print("--- DEBUG: Top of lighting/main.py has been executed. ---")

from lighting.api.main_router import lighting_router
from shared.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BellasReef Lighting API",
    description="API for managing lighting behaviors, effects, and hardware control",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include lighting router
print("--- DEBUG: About to include lighting_router... ---")
app.include_router(lighting_router)
print("--- DEBUG: Successfully included lighting_router. ---")

@app.get("/")
async def root():
    """Root endpoint providing basic service information."""
    return {
        "service": "BellasReef Lighting API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "lighting-api",
        "version": "2.0.0"
    }

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("BellasReef Lighting API Service starting up")
    logger.info(f"Service version: 2.0.0")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("BellasReef Lighting API Service shutting down")

# Export the app for uvicorn
__all__ = ["app"] 