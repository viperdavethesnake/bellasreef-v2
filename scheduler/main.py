#!/usr/bin/env python3
"""
Bella's Reef - Scheduler Service
Job scheduling, interval management, and device action coordination

This service handles:
- Schedule creation and management
- Job execution and timing
- Device action coordination
- Schedule calculation and validation
"""

import os
import sys
from pathlib import Path

# Add shared module to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from shared.core.config import settings
from shared.db.database import engine, Base
from scheduler.api import schedules
from scheduler.worker.scheduler_worker import SchedulerWorker

# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    print("🚀 Starting Bella's Reef Scheduler Service...")
    
    # Verify database connectivity and table existence
    try:
        async with engine.begin() as conn:
            # Test database connection
            await conn.execute(text("SELECT 1"))
            
            # Check if schedules table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'schedules'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                raise HTTPException(
                    status_code=500,
                    detail="Database tables not found. Please run 'python scripts/init_db.py' to initialize the database."
                )
        
        print("✅ Database connectivity verified")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}. Please ensure the database is running and initialized."
        )
    
    # Initialize scheduler worker
    scheduler_worker = SchedulerWorker()
    app.state.scheduler_worker = scheduler_worker
    
    # Start scheduler worker if enabled
    if os.getenv("SCHEDULER_WORKER_ENABLED", "true").lower() == "true":
        await scheduler_worker.start()
        print("✅ Scheduler worker started")
    
    print("✅ Scheduler service started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Scheduler service...")
    
    # Stop scheduler worker
    if hasattr(app.state, 'scheduler_worker'):
        await app.state.scheduler_worker.stop()

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Bella's Reef - Scheduler Service",
    description="Job scheduling, interval management, and device action coordination",
    version="1.0.0",
    lifespan=lifespan
)

# =============================================================================
# CORS Configuration
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API Routes
# =============================================================================

# Schedule management endpoints
app.include_router(schedules.router, prefix="/api/v1", tags=["schedules"])

# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Bella's Reef Scheduler Service",
        "version": "1.0.0",
        "description": "Job scheduling, interval management, and device action coordination",
        "endpoints": {
            "schedules": "/api/v1/schedules"
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
        "service": "Bella's Reef Scheduler Service",
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
        port=int(os.getenv("SERVICE_PORT", "8001")),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 