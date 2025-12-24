"""
Camera Models

Pydantic models for camera API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CameraBase(BaseModel):
    """Base camera model with common fields"""
    name: str = Field(..., description="Camera display name", example="Living Room Camera")
    ip_address: str = Field(..., description="Camera IP address", example="10.0.0.24")
    username: str = Field(..., description="Camera authentication username")
    password: str = Field(..., description="Camera authentication password")
    stream_quality: str = Field(default="stream2", description="Stream quality (stream1=HD, stream2=SD)", example="stream2")
    description: str = Field(default="", description="Camera description", example="Main living room camera")


class CameraCreateRequest(CameraBase):
    """Model for creating a new camera"""
    pass  # Inherits all fields from CameraBase


class CameraUpdate(BaseModel):
    """Model for updating an existing camera"""
    name: Optional[str] = Field(None, description="Camera display name")
    ip_address: Optional[str] = Field(None, description="Camera IP address")
    username: Optional[str] = Field(None, description="Camera authentication username")
    password: Optional[str] = Field(None, description="Camera authentication password")
    stream_quality: Optional[str] = Field(None, description="Stream quality (stream1=HD, stream2=SD)")
    description: Optional[str] = Field(None, description="Camera description")


class CameraCreateResponse(CameraBase):
    """Model for camera response from database"""
    camera_id: int = Field(..., description="Auto-generated camera identifier", example=1)
    created_at: datetime = Field(..., description="Camera creation timestamp")
    updated_at: datetime = Field(..., description="Camera last update timestamp")
    
    class Config:
        from_attributes = True


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
