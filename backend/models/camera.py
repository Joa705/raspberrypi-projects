"""
Camera Models

Pydantic models for camera API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any


class CameraResponse(BaseModel):
    """Response model for camera operations"""
    status: str = Field(..., description="Operation status", example="success")
    message: str = Field("", description="Human-readable message", example="Camera streaming started")
    data: Dict[str, Any] = Field(default={}, description="Additional response data")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed successfully",
                "data": {}
            }
        }


class SnapshotResponse(BaseModel):
    """Response model for camera snapshot"""
    status: str = Field(..., description="Capture status", example="success")
    image_data: str = Field(..., description="Image data (base64 or mock)", example="MOCK_IMAGE_DATA")
    format: str = Field(..., description="Image format", example="mock")
    timestamp: str = Field(..., description="ISO timestamp of capture", example="2025-12-23T10:30:00.123456")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "image_data": "MOCK_IMAGE_DATA",
                "format": "mock",
                "timestamp": "2025-12-23T10:30:00.123456"
            }
        }


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
