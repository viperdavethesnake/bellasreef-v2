import sys
from fastapi import FastAPI, Depends
from shared.core.config import settings
from shared.utils.logger import get_logger

logger = get_logger(__name__)

if not settings.TEMP_ENABLED:
    logger.info("Temperature Service is disabled. Set TEMP_ENABLED=true in temp/.env to enable.")
    sys.exit(0)

from .api import probes
from shared.api.deps import get_current_user
from shared.schemas.user import User

app = FastAPI(
    title="Bella's Reef - Temperature Service",
    description="Manages 1-wire temperature sensors.",
    version="1.0.0"
)

# app.include_router(probes.router, prefix="/api")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "temperature",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Bella's Reef Temperature Service",
        "version": "1.0.0",
        "description": "Manages 1-wire temperature sensors",
        "endpoints": {
            "probes": "/api/probes"
        }
    }