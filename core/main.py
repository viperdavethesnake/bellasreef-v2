#!/usr/bin/env python3
"""
Bella's Reef - Core Service
User authentication, session management, and system health APIs

This service handles:
- User authentication and registration
- Session management and JWT tokens
- System health monitoring
- User management and permissions
"""

import os
import sys
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from shared.core.config import settings
from shared.db.database import engine, Base, async_session
from shared.db.models import User
from shared.utils.logger import get_logger
from core.api import health, auth, users, deps, system_info

logger = get_logger(__name__)

# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("🚀 Starting Bella's Reef Core Service...")
    
    # Verify database connectivity and table existence
    try:
        async with engine.begin() as conn:
            # Test database connection
            await conn.execute(text("SELECT 1"))
            
            # Check if users table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                raise HTTPException(
                    status_code=500,
                    detail="Database tables not found. Please run 'python scripts/init_db.py' to initialize the database."
                )
        
        logger.info("✅ Database connectivity verified")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}. Please ensure the database is running and initialized."
        )
    
    logger.info("✅ Core service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Core service...")

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Bella's Reef - Core Service",
    description="User authentication, session management, and system health APIs",
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

# Health endpoints
app.include_router(health.router, tags=["health"])

# Authentication endpoints
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])

# User management endpoints
app.include_router(users.router, prefix="/api/users", tags=["users"])

# System information endpoints
app.include_router(system_info.router, prefix="/api", tags=["system"])

# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Bella's Reef Core Service",
        "version": "1.0.0",
        "description": "User authentication, session management, and system health APIs",
        "endpoints": {
            "health": "/api/health",
            "auth": "/api/auth",
            "users": "/api/users"
        }
    }

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Check if service is enabled
    if not settings.CORE_ENABLED:
        logger.info("Core Service is disabled. Set CORE_ENABLED=true in core/.env to enable.")
        sys.exit(0)
    
    uvicorn.run(
        "main:app",
        host=os.getenv("SERVICE_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVICE_PORT", "8000")),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 