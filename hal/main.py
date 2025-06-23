"""
Bella's Reef - HAL Service
Main FastAPI application for the Hardware Abstraction Layer.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.core.config import settings

# Import the new router
from .api import pca9685

# --- FastAPI App Configuration ---
app = FastAPI(
    title="Bella's Reef - HAL Service",
    description="Provides a unified API to control low-level hardware like PWM controllers and GPIO relays.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---
# Include the new PCA9685 router
app.include_router(pca9685.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "service": "Bella's Reef HAL Service",
        "description": "Ready to control hardware.",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hal"}

# --- Main Entry Point ---
if __name__ == "__main__":
    uvicorn.run(
        "hal.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT_HAL, # We will add this setting next
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 