"""
Heat Sensor Models

Pydantic models for heat sensor API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TemperatureResponse(BaseModel):
    """Response model for temperature readings"""
    temperature_celsius: Optional[float] = Field(None, description="Temperature in Celsius", example=22.5)
    humidity_percent: Optional[float] = Field(None, description="Relative humidity percentage", example=55.2)
    timestamp: str = Field(..., description="ISO timestamp of reading", example="2025-12-23T10:30:00.123456")
    status: str = Field(..., description="Reading status", example="success")

    class Config:
        json_schema_extra = {
            "example": {
                "temperature_celsius": 22.5,
                "humidity_percent": 55.2,
                "timestamp": "2025-12-23T10:30:00.123456",
                "status": "success"
            }
        }
