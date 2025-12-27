"""
FastAPI Backend - Main Application Entry Point

This is the main FastAPI application that runs on a Raspberry Pi.
It coordinates hardware modules (camera, heat sensor, light) and
exposes a REST API for a Svelte frontend.

This is a single-process application, not a microservices architecture.
"""

import logging
import sys
import psutil
import time
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from schemas.system import SystemInfo
from api import camera
from database.db import init_db

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    logger.info("Starting FastAPI backend...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down...")

# Create FastAPI application
app = FastAPI(
    title="Raspberry Pi Hardware Control API",
    description="""Backend API for controlling Raspberry Pi hardware modules""",
    lifespan=lifespan,
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
app.include_router(camera.router, prefix="/cameras", tags=["Camera"])

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


@app.get("/system-info", response_model=SystemInfo)
async def system_info():
    """
    Get comprehensive system information about the Raspberry Pi.
    
    Returns CPU, RAM, disk usage, temperature, uptime, and camera stream status.
    """
    # CPU Information
    cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)  # Per-core usage
    cpu_percent = sum(cpu_per_core) / len(cpu_per_core)  # Calculate average from per-core
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    load_avg = psutil.getloadavg()
    
    # Memory Information
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    # Disk Information
    disk = psutil.disk_usage('/')
    
    # System Temperature (Raspberry Pi specific)
    temperature = None
    try:
        # Try to read Raspberry Pi CPU temperature
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp_c = int(f.read().strip()) / 1000.0
            temperature = {
                "celsius": round(temp_c, 1),
                "fahrenheit": round(temp_c * 9/5 + 32, 1)
            }
    except (FileNotFoundError, PermissionError):
        # Fall back to psutil sensors if available
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # Get the first available temperature sensor
                for name, entries in temps.items():
                    if entries:
                        temp_c = entries[0].current
                        temperature = {
                            "celsius": round(temp_c, 1),
                            "fahrenheit": round(temp_c * 9/5 + 32, 1),
                            "sensor": name
                        }
                        break
        except:
            pass
    
    # System Uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_seconds = (datetime.now() - boot_time).total_seconds()
    uptime_hours = uptime_seconds / 3600
    
    # Camera stream information
    from modules.camera.controller import get_camera_controller
    controller = get_camera_controller()
    camera_stats = controller.get_all_status()
    total_viewers = sum(cam['viewer_count'] for cam in camera_stats.values())
    active_streams = sum(1 for cam in camera_stats.values() if cam['is_running'])
    
    return SystemInfo(
        timestamp=datetime.now().isoformat(),
        cpu={
            "usage_percent": round(cpu_percent, 1),
            "per_core": [round(core, 1) for core in cpu_per_core],
            "cores": cpu_count,
            "frequency_mhz": round(cpu_freq.current, 1) if cpu_freq else None,
            "load_average": {
                "1min": round(load_avg[0], 2),
                "5min": round(load_avg[1], 2),
                "15min": round(load_avg[2], 2)
            }
        },
        memory={
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent": memory.percent
        },
        swap={
            "total_gb": round(swap.total / (1024**3), 2),
            "used_gb": round(swap.used / (1024**3), 2),
            "percent": swap.percent
        },
        disk={
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        },
        temperature=temperature,
        uptime={
            "seconds": round(uptime_seconds),
            "hours": round(uptime_hours, 1),
            "boot_time": boot_time.isoformat()
        },
        cameras={
            "active_streams": active_streams,
            "total_viewers": total_viewers,
            "total_cameras": len(camera_stats)
        }
    )
    
   
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
