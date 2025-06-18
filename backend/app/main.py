from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Import and include routers
# from app.api import auth, lights, outlets, sensors, system
# app.include_router(auth.router)
# app.include_router(lights.router)
# app.include_router(outlets.router)
# app.include_router(sensors.router)
# app.include_router(system.router) 