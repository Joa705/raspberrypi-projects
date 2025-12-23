"""
FastAPI Backend - Main Application Entry Point

This is the main FastAPI application that runs on a Raspberry Pi.
It coordinates hardware modules (camera, heat sensor, light) and
exposes a REST API for a Svelte frontend.

This is a single-process application, not a microservices architecture.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from api import camera, heat, light

# Create FastAPI application
app = FastAPI(
    title="Raspberry Pi Hardware Control API",
    description="""Backend API for controlling Raspberry Pi hardware modules.
    
    This API provides endpoints to control:
    - **Camera**: Capture snapshots and manage video streaming
    - **Heat Sensor**: Read temperature and humidity data
    - **Light**: Control relay-connected lighting
    
    All endpoints return JSON responses suitable for frontend consumption.
    """,
    version="1.0.0",
    contact={
        "name": "Raspberry Pi Projects",
        "url": "https://github.com/yourusername/raspberrypi-projects",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "Camera",
            "description": "Operations for camera control, including snapshots and streaming",
        },
        {
            "name": "Heat Sensor",
            "description": "Temperature and humidity sensor readings",
        },
        {
            "name": "Light",
            "description": "Control relay-connected lights (on/off/toggle)",
        },
    ]
)

# Configure CORS for Svelte frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(camera.router, prefix="/camera", tags=["Camera"])
app.include_router(heat.router, prefix="/heat", tags=["Heat Sensor"])
app.include_router(light.router, prefix="/light", tags=["Light"])

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint providing API information
    """
    return {
        "name": "Raspberry Pi Hardware Control API",
        "version": "1.0.0",
        "status": "running",
        "modules": ["camera", "heat", "light"]
    }

# Health check endpoint
@app.get("/health")
async def health():
    """
    Health check endpoint for monitoring
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
