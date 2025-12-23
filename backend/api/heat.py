"""
Heat Sensor API Routes

This module defines FastAPI routes for heat sensor operations.
It imports and uses the heat sensor hardware module but contains no hardware logic itself.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

# Import heat sensor hardware module
from modules.heat import HeatSensor

# Import models
from models.heat import TemperatureResponse

import logging

# Create API router
router = APIRouter()

# Create a single heat sensor instance
heat_sensor = HeatSensor()

logger = logging.getLogger(__name__)

@router.get(
    "/",
    response_model=TemperatureResponse,
    responses={
        200: {"description": "Sensor reading retrieved successfully"},
        500: {"description": "Failed to read sensor"}
    }
)
async def get_temperature():
    """
    Get current temperature and humidity reading.
    
    Reads both temperature (Celsius) and humidity (percentage) from the sensor
    in a single call. Returns mock data in development mode.
    
    Returns:
        Combined temperature and humidity reading with timestamp
    """
    try:
        reading = heat_sensor.get_reading()
        
        return JSONResponse(
            status_code=200,
            content=reading
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading sensor: {str(e)}"
        )


@router.get("/temperature")
async def get_temperature_only():
    """
    GET /heat/temperature
    
    Get only the temperature reading (no humidity).
    
    Returns:
        Dict: Temperature value and timestamp
    """
    try:
        temperature = heat_sensor.read_temperature()
        
        if temperature is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to read temperature"
            )
        
        from datetime import datetime
        return JSONResponse(
            status_code=200,
            content={
                "temperature_celsius": temperature,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading temperature: {str(e)}"
        )


@router.get("/humidity")
async def get_humidity_only():
    """
    GET /heat/humidity
    
    Get only the humidity reading (no temperature).
    
    Returns:
        Dict: Humidity value and timestamp
    """
    try:
        humidity = heat_sensor.read_humidity()
        
        if humidity is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to read humidity"
            )
        
        from datetime import datetime
        return JSONResponse(
            status_code=200,
            content={
                "humidity_percent": humidity,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading humidity: {str(e)}"
        )
