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
    sets channel 0 to 100% and channel 1 to 0%, and returns results.
    """
    import traceback
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    
    result = {
        "success": False,
        "address": hex(address),
        "steps": [],
        "error": None,
        "traceback": None
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
        
        # Step 3: Set channel 0 to 100% (duty cycle 65535)
        result["steps"].append("Setting channel 0 to 100% (duty cycle 65535)")
        pca.channels[0].duty_cycle = 65535
        result["steps"].append("Channel 0 set to 100% successfully")
        
        # Step 4: Set channel 1 to 0% (duty cycle 0)
        result["steps"].append("Setting channel 1 to 0% (duty cycle 0)")
        pca.channels[1].duty_cycle = 0
        result["steps"].append("Channel 1 set to 0% successfully")
        
        # Step 5: Verify the settings
        result["steps"].append("Verifying channel settings")
        channel_0_duty = pca.channels[0].duty_cycle
        channel_1_duty = pca.channels[1].duty_cycle
        
        result["steps"].append(f"Channel 0 duty cycle: {channel_0_duty}")
        result["steps"].append(f"Channel 1 duty cycle: {channel_1_duty}")
        
        # Step 6: Cleanup
        result["steps"].append("Cleaning up I2C bus")
        i2c_bus.deinit()
        result["steps"].append("I2C bus deinitialized successfully")
        
        result["success"] = True
        result["final_state"] = {
            "channel_0_duty_cycle": channel_0_duty,
            "channel_1_duty_cycle": channel_1_duty,
            "channel_0_percentage": round((channel_0_duty / 65535) * 100, 2),
            "channel_1_percentage": round((channel_1_duty / 65535) * 100, 2)
        }
        
        logger.info(f"PCA9685 debug test successful for address {hex(address)}")
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        result["exception_type"] = type(e).__name__
        
        logger.error(f"PCA9685 debug test failed for address {hex(address)}: {e}")
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