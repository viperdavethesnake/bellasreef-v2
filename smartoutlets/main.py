#!/usr/bin/env python3
"""
Bella's Reef - SmartOutlets Service
Smart outlet management, control, and discovery APIs

This service handles:
- Smart outlet registration and configuration
- Real-time outlet control (on/off/toggle)
- Device discovery (local and cloud)
- Outlet state monitoring and telemetry
- Driver management for multiple smart outlet brands
"""

import os
import sys
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from shared.db.database import engine, Base, async_session
from shared.utils.logger import get_logger
from .config import settings
from .api import router, vesync_router
from .handlers import register_exception_handlers
from .manager import SmartOutletManager

# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger = get_logger(__name__)
    logger.info("🚀 Starting Bella's Reef SmartOutlets Service...")
    
    # Verify database connectivity and table existence
    try:
        async with engine.begin() as conn:
            # Test database connection
            await conn.execute(text("SELECT 1"))
            
            # Check if smart_outlets table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'smart_outlets'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                raise HTTPException(
                    status_code=500,
                    detail="SmartOutlets table not found. Please run 'python scripts/init_db.py' to initialize the database."
                )
        
        logger.info("✅ Database connectivity verified")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}. Please ensure the database is running and initialized."
        )
    
    logger.info("✅ SmartOutlets service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SmartOutlets service...")

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Bella's Reef - SmartOutlets Service",
    description="Smart outlet management, control, and discovery APIs",
    version="1.0.0",
    lifespan=lifespan
)

# =============================================================================
# CORS Configuration
# =============================================================================

# Use permissive CORS for development - can be made more restrictive in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure specific origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Exception Handlers
# =============================================================================

# Register SmartOutlet exception handlers
register_exception_handlers(app)

# =============================================================================
# API Routes
# =============================================================================

# Include SmartOutlet API routes
app.include_router(router, prefix="/api/smartoutlets", tags=["smartoutlets"])

# Include VeSync Account Management routes
app.include_router(vesync_router, prefix="/api/smartoutlets", tags=["smartoutlets"])

# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Bella's Reef SmartOutlets Service",
        "version": "1.0.0",
        "description": "Smart outlet management, control, and discovery APIs",
        "endpoints": {
            "smartoutlets": "/api/smartoutlets"
        },
        "features": [
            "Outlet registration and configuration",
            "Real-time outlet control",
            "Device discovery (local and cloud)",
            "State monitoring and telemetry"
        ]
    }

# =============================================================================
# Health Check Endpoint
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for the SmartOutlets service."""
    return {
        "status": "healthy",
        "service": "smartoutlets",
        "version": "1.0.0"
    }

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Check if service is enabled
    if not settings.SMART_OUTLETS_ENABLED:
        print("SmartOutlets Service is disabled. Set SMART_OUTLETS_ENABLED=true in smartoutlets/.env to enable.")
        sys.exit(0)
    
    uvicorn.run(
        "main:app",
        host=os.getenv("SERVICE_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVICE_PORT", "8000")),
        reload=False,  # Disable reload for production safety
        log_level="info"
    ) 