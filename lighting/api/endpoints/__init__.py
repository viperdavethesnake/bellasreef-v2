"""
Lighting API endpoints package.
"""
from .behaviors import router as behavior_router
from .groups import router as group_router
from .assignments import router as assignment_router
from .logs import router as log_router

__all__ = [
    "behavior_router",
    "group_router", 
    "assignment_router",
    "log_router"
] 