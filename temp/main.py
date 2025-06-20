import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add project root to Python path for shared imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from temp.config import settings

# Check if service is enabled
if not settings.TEMP_ENABLED:
    print("❌ Temperature Service is disabled.")
    print("   Set TEMP_ENABLED=true in /temp/.env to enable the service.")
    print("   Exiting immediately.")
    sys.exit(0)

from temp.api.probes import router as probes_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the temperature service.
    """
    # Startup
    print("🌡️  Starting Bella's Reef Temperature Service...")
    print(f"   📍 Service will run on {settings.SERVICE_HOST}:{settings.SERVICE_PORT}")
    print(f"   🔧 Debug mode: {settings.DEBUG}")
    print(f"   📊 Log level: {settings.LOG_LEVEL}")
    
    # Check 1-wire subsystem availability
    from temp.services.temperature import temperature_service
    check_result = temperature_service.check_1wire_subsystem()
    
    if check_result.subsystem_available:
        print(f"   ✅ 1-wire subsystem: Available ({check_result.device_count} sensors)")
        if check_result.details:
            print(f"      {check_result.details}")
    else:
        print(f"   ⚠️  1-wire subsystem: {check_result.error}")
        if check_result.details:
            print(f"      {check_result.details}")
    
    print("   🚀 Temperature service ready!")
    yield
    
    # Shutdown
    print("🛑 Shutting down Temperature Service...")

# Create FastAPI application
app = FastAPI(
    title="Bella's Reef Temperature Service",
    description="""
    Temperature probe management and monitoring service for Bella's Reef.
    
    This service provides:
    - 1-wire temperature sensor discovery and management
    - Real-time temperature readings
    - Probe configuration and status tracking
    - Hardware subsystem diagnostics
    
    ## Authentication
    
    Most endpoints require authentication using a Bearer token.
    Set the `SERVICE_TOKEN` environment variable and include it in requests:
    
    ```
    Authorization: Bearer your_service_token_here
    ```
    
    ## Hardware Requirements
    
    - Raspberry Pi with 1-wire temperature sensors (DS18B20)
    - 1-wire bus enabled in `/boot/config.txt`
    - Temperature sensors connected to GPIO 4 (default)
    
    ## Setup
    
    1. Enable 1-wire in `/boot/config.txt`: `dtoverlay=w1-gpio,gpiopin=4`
    2. Reboot the Raspberry Pi
    3. Connect temperature sensors
    4. Configure the service using the provided endpoints
    """,
    version="1.0.0",
    contact={
        "name": "Bella's Reef",
        "url": "https://github.com/your-repo/bellasreef-v2",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(probes_router)

@app.get("/", summary="Service root")
async def root():
    """
    Service root endpoint.
    
    Returns basic service information and status.
    """
    from temp.services.temperature import temperature_service
    
    # Check 1-wire subsystem
    check_result = temperature_service.check_1wire_subsystem()
    
    return {
        "service": "Bella's Reef Temperature Service",
        "version": "1.0.0",
        "status": "running",
        "hardware": {
            "1wire_available": check_result.subsystem_available,
            "sensor_count": check_result.device_count,
            "gpio_pin": settings.W1_GPIO_PIN,
            "error": check_result.error
        },
        "endpoints": {
            "probe_discovery": "/probe/discover",
            "probe_management": "/probe/",
            "hardware_check": "/probe/check",
            "docs": "/docs"
        },
        "authentication": "Bearer token required for most endpoints"
    }

@app.get("/health", summary="Health check")
async def health_check():
    """
    Health check endpoint.
    
    Returns service health status and basic diagnostics.
    """
    from temp.services.temperature import temperature_service
    
    # Check 1-wire subsystem
    check_result = temperature_service.check_1wire_subsystem()
    
    # Determine overall health
    health_status = "healthy" if check_result.subsystem_available else "degraded"
    
    return {
        "status": health_status,
        "service": "temperature",
        "timestamp": "2024-01-01T00:00:00Z",  # Would use real timestamp in production
        "hardware": {
            "1wire_available": check_result.subsystem_available,
            "sensor_count": check_result.device_count,
            "error": check_result.error
        }
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Custom HTTP exception handler.
    
    Provides consistent error responses across the service.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "service": "temperature"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    General exception handler.
    
    Catches unexpected errors and provides safe error responses.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "status_code": 500,
            "service": "temperature"
        }
    )

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "temp.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    ) 