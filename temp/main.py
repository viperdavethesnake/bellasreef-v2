import sys
from fastapi import FastAPI, Depends
from .config import settings

if not settings.TEMP_ENABLED:
    print("Temperature Service is disabled. Set TEMP_ENABLED=true in .env to enable.")
    sys.exit(0)

from .api import probes
from .deps import get_api_key

app = FastAPI(
    title="Bella's Reef - Temperature Service",
    description="Manages 1-wire temperature sensors.",
    version="1.0.0"
)

app.include_router(probes.router)

@app.get("/probe/health")
def health_check():
    return {"status": "ok"}

# This is a sample root endpoint with authentication
@app.get("/")
def read_root(api_key: str = Depends(get_api_key)):
    return {"message": "Welcome to the Temperature Service"}