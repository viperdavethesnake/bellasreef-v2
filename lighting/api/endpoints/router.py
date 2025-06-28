"""
Main router for lighting API endpoints.
"""
from fastapi import APIRouter

from .behaviors import router as behaviors_router
from .groups import router as groups_router
from .assignments import router as assignments_router
from .logs import router as logs_router

# Create main lighting router
lighting_router = APIRouter(prefix="/lighting", tags=["lighting"])

# Include all sub-routers
lighting_router.include_router(behaviors_router)
lighting_router.include_router(groups_router)
lighting_router.include_router(assignments_router)
lighting_router.include_router(logs_router) 