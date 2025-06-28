"""
Main Lighting API Router.

This module provides the main FastAPI router that includes all lighting-related endpoints:
- Behavior management (CRUD operations)
- Assignment management (assigning behaviors to channels/groups)
- Group management (CRUD operations)
- Log management (viewing behavior logs)
- Runner control (channel registration, hardware control)
- Effects and overrides management
- Scheduler control (start/stop/monitoring)

All endpoints use the real HAL layer for hardware control.
"""
from fastapi import APIRouter

from lighting.api.endpoints import (
    behavior_router,
    assignment_router,
    group_router,
    log_router
)
from lighting.api.runner import router as runner_router
from lighting.api.effects import router as effects_router
from lighting.api.scheduler import router as scheduler_router

# Create main lighting router
lighting_router = APIRouter(prefix="/lighting", tags=["Lighting System"])

# Include all lighting endpoints
lighting_router.include_router(behavior_router, prefix="/behaviors")
lighting_router.include_router(assignment_router, prefix="/assignments")
lighting_router.include_router(group_router, prefix="/groups")
lighting_router.include_router(log_router, prefix="/logs")
lighting_router.include_router(runner_router, prefix="/runner")
lighting_router.include_router(effects_router, prefix="/effects")
lighting_router.include_router(scheduler_router, prefix="/scheduler")

# Export the main router
__all__ = ["lighting_router"] 