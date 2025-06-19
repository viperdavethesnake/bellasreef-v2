#!/usr/bin/env python3
"""
Bella's Reef - Control Service
PWM, relay, and GPIO output control for hardware devices

This service handles:
- PWM control for lights, pumps, and other devices
- GPIO output control for relays and switches
- Hardware device management
- Device state control and monitoring
"""

import os
import sys
from pathlib import Path

# Add shared module to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from shared.core.config import settings
from shared.db.database import engine, Base
from control.api import devices
from control.hardware.device_factory import DeviceFactory
from shared.db.models import Device

# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    print("🚀 Starting Bella's Reef Control Service...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize hardware factory
    device_factory = DeviceFactory()
    app.state.device_factory = device_factory
    
    print("✅ Control service started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Control service...")

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Bella's Reef Control Service",
    description="PWM, relay, and GPIO hardware control",
    version="1.0.0",
    lifespan=lifespan
)

# =============================================================================
# CORS Configuration
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API Routes
# =============================================================================

# Device control endpoints
app.include_router(devices.router, prefix="/api/v1", tags=["devices"])

# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Bella's Reef Control Service",
        "version": "1.0.0",
        "description": "PWM, relay, and GPIO output control for hardware devices",
        "endpoints": {
            "devices": "/api/v1/devices"
        }
    }

# =============================================================================
# Health Endpoint
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Bella's Reef Control Service",
        "version": "1.0.0"
    }

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=os.getenv("SERVICE_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVICE_PORT", "8003")),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 