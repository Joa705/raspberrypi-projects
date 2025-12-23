"""
Camera Models

Pydantic models for camera API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any


# keepings this as an example for future use
class CameraStatusResponse(BaseModel):
    """Response model for camera status"""
    initialized: bool = Field(..., description="Whether camera is initialized", example=True)
    streaming: bool = Field(..., description="Whether camera is currently streaming", example=False)
    active: bool = Field(..., description="Whether camera is active", example=True)

    class Config:
        json_schema_extra = {
            "example": {
                "initialized": True,
                "streaming": False,
                "active": True
            }
        }
