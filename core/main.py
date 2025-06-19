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

# Add shared module to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from shared.core.config import settings
from shared.db.database import engine, Base
from shared.db.models import User
from core.api import health, auth, users, deps

# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    print("🚀 Starting Bella's Reef Core Service...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Core service started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Core service...")

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
    
    uvicorn.run(
        "main:app",
        host=os.getenv("SERVICE_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVICE_PORT", "8000")),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 