# --- ALL OTHER IMPORTS AND CODE MUST BE BELOW THIS LINE ---

"""
Bella's Reef - HAL Service
Main FastAPI application for the Hardware Abstraction Layer.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.core.config import settings
from shared.utils.logger import get_logger

# Import the new routers
from .api import controllers, channels
from .drivers.pca9685_driver import get_manager, cleanup_manager

logger = get_logger(__name__)

# --- FastAPI App Configuration ---
app = FastAPI(
    title="Bella's Reef - HAL Service",
    description="Provides a unified API to control low-level hardware like PWM controllers and GPIO relays.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FastAPI Lifecycle Events ---
@app.on_event("startup")
async def startup_event():
    """Initialize hardware manager on service startup."""
    logger.info("HAL Service: Starting up - initializing hardware manager")
    try:
        # Initialize the PCA9685 manager singleton
        manager = get_manager()
        logger.info("HAL Service: Hardware manager initialized successfully")
        logger.info(f"HAL Service: Manager status: {manager.get_status()}")
    except Exception as e:
        logger.error(f"HAL Service: Failed to initialize hardware manager: {e}")
        # Don't raise - allow service to start even if hardware is unavailable

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up hardware manager on service shutdown."""
    logger.info("HAL Service: Shutting down - cleaning up hardware manager")
    try:
        cleanup_manager()
        logger.info("HAL Service: Hardware manager cleanup completed")
    except Exception as e:
        logger.error(f"HAL Service: Error during hardware manager cleanup: {e}")

# --- API Endpoints ---
# Include the new routers
app.include_router(controllers.router, prefix="/api/hal")
app.include_router(channels.router, prefix="/api/hal")

@app.get("/")
async def root():
    return {
        "service": "Bella's Reef HAL Service",
        "description": "Ready to control hardware.",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Enhanced health check that includes hardware manager status."""
    try:
        manager = get_manager()
        manager_status = manager.get_status()
        return {
            "status": "healthy", 
            "service": "hal",
            "hardware_manager": manager_status
        }
    except Exception as e:
        return {
            "status": "degraded", 
            "service": "hal",
            "error": f"Hardware manager error: {str(e)}"
        }

@app.get("/debug/hardware-manager")
async def debug_hardware_manager():
    """Debug endpoint to check hardware manager status and configuration."""
    try:
        manager = get_manager()
        status = manager.get_status()
        return {
            "hardware_manager_status": status,
            "manager_instance_id": id(manager),
            "manager_class": manager.__class__.__name__
        }
    except Exception as e:
        return {
            "error": f"Failed to get hardware manager status: {str(e)}",
            "exception_type": type(e).__name__
        }

# --- Main Entry Point ---
if __name__ == "__main__":
    uvicorn.run(
        "hal.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT_HAL, # We will add this setting next
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 