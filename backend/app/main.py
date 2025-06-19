from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI(
    title="Bella's Reef API",
    description="Backend API for reef tank automation and monitoring",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Bella's Reef API"}

@app.on_event("startup")
async def startup_event():
    """Start the device poller service on application startup"""
    from app.services.poller import poller
    # Start poller in background task
    asyncio.create_task(poller.start())

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the device poller service on application shutdown"""
    from app.services.poller import poller
    await poller.stop()

# Import and include routers
from app.api import auth, users, health, devices

# API v1 routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1/devices")

# Health check router (no version prefix)
app.include_router(health.router) 