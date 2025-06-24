import sys
from fastapi import FastAPI, Depends
from shared.core.config import settings

if not settings.TEMP_ENABLED:
    print("Temperature Service is disabled. Set TEMP_ENABLED=true in temp/.env to enable.")
    sys.exit(0)

from .api import probes
from core.api.deps import get_current_user
from shared.schemas.user import User

app = FastAPI(
    title="Bella's Reef - Temperature Service",
    description="Manages 1-wire temperature sensors.",
    version="1.0.0"
)

app.include_router(probes.router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "temperature",
        "version": "1.0.0"
    }

# This is a sample root endpoint with authentication
@app.get("/")
def read_root(current_user: User = Depends(get_current_user)):
    return {"message": "Welcome to the Temperature Service"}