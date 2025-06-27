# --- ALL OTHER IMPORTS AND CODE MUST BE BELOW THIS LINE ---

"""
Bella's Reef - HAL Service
Main FastAPI application for the Hardware Abstraction Layer.
"""
import uvicorn
from fastapi import FastAPI, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from shared.core.config import settings
from shared.utils.logger import get_logger
import asyncio
import threading

# Import the new routers
from .api import controllers, channels
from .drivers.pca9685_driver import get_manager, cleanup_manager
from .deps import get_current_user_or_service
from shared.schemas.user import User
from .api.channels import execute_pending_ramp_steps

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

# Global variable to control the background task
_ramp_executor_running = False
_ramp_executor_task = None

async def ramp_executor_background_task():
    """Background task to execute pending ramp steps from the main thread."""
    global _ramp_executor_running
    _ramp_executor_running = True
    
    while _ramp_executor_running:
        try:
            # Execute any pending ramp steps
            execute_pending_ramp_steps()
            
            # Sleep for a short interval (50ms) to avoid blocking
            await asyncio.sleep(0.05)
            
        except Exception as e:
            logger.error(f"Error in ramp executor background task: {e}")
            await asyncio.sleep(1)  # Longer sleep on error

# --- FastAPI Lifecycle Events ---
@app.on_event("startup")
async def startup_event():
    """Initialize hardware manager on service startup."""
    global _ramp_executor_task
    
    logger.info("HAL Service: Starting up - initializing hardware manager")
    try:
        # Initialize the PCA9685 manager singleton
        manager = get_manager()
        logger.info("HAL Service: Hardware manager initialized successfully")
        logger.info(f"HAL Service: Manager status: {manager.get_status()}")
        
        # Start the ramp executor background task
        _ramp_executor_task = asyncio.create_task(ramp_executor_background_task())
        logger.info("HAL Service: Ramp executor background task started")
        
    except Exception as e:
        logger.error(f"HAL Service: Failed to initialize hardware manager: {e}")
        # Don't raise - allow service to start even if hardware is unavailable

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up hardware manager on service shutdown."""
    global _ramp_executor_running, _ramp_executor_task
    
    logger.info("HAL Service: Shutting down - cleaning up hardware manager")
    
    # Stop the ramp executor background task
    _ramp_executor_running = False
    if _ramp_executor_task:
        _ramp_executor_task.cancel()
        try:
            await _ramp_executor_task
        except asyncio.CancelledError:
            pass
        logger.info("HAL Service: Ramp executor background task stopped")
    
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

@app.post("/api/debug/pca-test", status_code=status.HTTP_200_OK)
async def debug_pca_test(
    address: int = 0x40,
    current_user: User = Depends(get_current_user_or_service)
):
    """
    Debug endpoint to test PCA9685 instantiation and basic functionality.
    Instantiates a PCA9685 using busio.I2C(board.SCL, board.SDA),
    sets frequency to 1000, fades channel 0 up and channel 1 down, then turns both off.
    Returns detailed results.
    """
    import traceback
    import board
    import busio
    import time
    from adafruit_pca9685 import PCA9685

    result = {
        "success": False,
        "address": hex(address),
        "steps": [],
        "error": None,
        "traceback": None,
        "fade_log": []
    }

    try:
        # Step 1: Create I2C bus
        result["steps"].append("Creating I2C bus with busio.I2C(board.SCL, board.SDA)")
        i2c_bus = busio.I2C(board.SCL, board.SDA)
        result["steps"].append("I2C bus created successfully")

        # Step 2: Create PCA9685 instance
        result["steps"].append(f"Creating PCA9685 instance at address {hex(address)}")
        pca = PCA9685(i2c_bus, address=address)
        result["steps"].append("PCA9685 instance created successfully")

        # Step 3: Set frequency to 1000
        result["steps"].append("Setting frequency to 1000 Hz")
        pca.frequency = 1000
        result["steps"].append(f"Frequency set to {pca.frequency} Hz")

        # Step 4: Fade Ch0 up and Ch1 down
        steps = 100
        delay = 0.03
        result["steps"].append("Fading Ch0 up and Ch1 down...")
        for i in range(steps + 1):
            duty_ch0 = int(65535 * (i / steps))
            duty_ch1 = int(65535 * ((steps - i) / steps))
            pca.channels[0].duty_cycle = duty_ch0
            pca.channels[1].duty_cycle = duty_ch1
            # Optionally log a few steps for diagnostics
            if i in (0, steps//2, steps):
                result["fade_log"].append({"step": i, "ch0": duty_ch0, "ch1": duty_ch1})
            time.sleep(delay)

        # Step 5: Turn both channels off
        result["steps"].append("Turning both channels off.")
        pca.channels[0].duty_cycle = 0
        pca.channels[1].duty_cycle = 0

        # Step 6: Read back final values
        ch0_final = pca.channels[0].duty_cycle
        ch1_final = pca.channels[1].duty_cycle
        result["steps"].append(f"Final channel values: ch0={ch0_final}, ch1={ch1_final}")

        # Step 7: Cleanup
        result["steps"].append("Cleaning up I2C bus")
        i2c_bus.deinit()
        result["steps"].append("I2C bus deinitialized successfully")

        result["success"] = True
        result["final_state"] = {
            "channel_0_duty_cycle": ch0_final,
            "channel_1_duty_cycle": ch1_final,
            "channel_0_percentage": round((ch0_final / 65535) * 100, 2),
            "channel_1_percentage": round((ch1_final / 65535) * 100, 2)
        }

        logger.info(f"PCA9685 debug test (fade) successful for address {hex(address)}")

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        result["exception_type"] = type(e).__name__

        logger.error(f"PCA9685 debug test (fade) failed for address {hex(address)}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

    return result

# --- Main Entry Point ---
if __name__ == "__main__":
    uvicorn.run(
        "hal.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT_HAL, # We will add this setting next
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 