#!/usr/bin/env python3
"""
Bella's Reef - Poller Service
Device polling, sensor data collection, and alert evaluation

This service handles:
- Device polling and data collection
- Sensor data storage and retrieval
- Alert evaluation and triggering
- Device status monitoring
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
from shared.db.models import Device, Alert, History
import poller.api.devices as devices
import poller.api.alerts as alerts
from poller.services.poller import DevicePoller
from poller.worker.alert_worker import AlertWorker

# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    print("🚀 Starting Bella's Reef Poller Service...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize poller
    device_poller = DevicePoller()
    app.state.device_poller = device_poller
    
    # Initialize alert worker
    alert_worker = AlertWorker()
    app.state.alert_worker = alert_worker
    
    # Start poller if enabled
    if os.getenv("POLLER_WORKER_ENABLED", "true").lower() == "true":
        await device_poller.start()
        print("✅ Device poller started")
    
    # Start alert worker if enabled
    if os.getenv("ALERT_WORKER_ENABLED", "true").lower() == "true":
        await alert_worker.start()
        print("✅ Alert worker started")
    
    print("✅ Poller service started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Poller service...")
    
    # Stop poller
    if hasattr(app.state, 'device_poller'):
        await app.state.device_poller.stop()
    
    # Stop alert worker
    if hasattr(app.state, 'alert_worker'):
        await app.state.alert_worker.stop()

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Bella's Reef - Poller Service",
    description="Device polling, sensor data collection, and alert management",
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

# Device management endpoints
app.include_router(devices.router, prefix="/api/devices", tags=["devices"])

# Alert management endpoints
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])

# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Bella's Reef Poller Service",
        "version": "1.0.0",
        "description": "Device polling, sensor data collection, and alert evaluation",
        "endpoints": {
            "devices": "/api/devices",
            "alerts": "/api/alerts"
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
        "service": "Bella's Reef Poller Service",
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
        port=int(os.getenv("SERVICE_PORT", "8002")),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 