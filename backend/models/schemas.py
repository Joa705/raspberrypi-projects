"""
Pydantic schemas for module and camera API.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


# ============================================================================
# Module Schemas
# ============================================================================

class ModuleRegister(BaseModel):
    """Schema for registering a new module."""
    module_id: str = Field(..., description="Unique module identifier")
    module_type: str = Field(..., description="Module type (camera, sensor, heat, etc.)")
    name: str = Field(..., description="Module name")
    description: Optional[str] = Field(None, description="Module description")
    url: str = Field(..., description="Module service URL")


class ModuleResponse(BaseModel):
    """Schema for module responses."""
    id: int
    module_id: str
    module_type: str
    name: str
    description: Optional[str]
    url: str
    status: str
    last_seen: Optional[datetime]
    registered_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModuleStatusUpdate(BaseModel):
    """Schema for updating module status."""
    status: str = Field(..., description="Module status (online, offline, error)")


# ============================================================================
# Camera Schemas
# ============================================================================

class CameraRegister(BaseModel):
    """Schema for registering a camera."""
    camera_id: str = Field(..., description="Unique camera identifier")
    name: str = Field(..., description="Camera name")
    module_id: int = Field(..., description="ID of the module managing this camera")
    stream_url: str = Field(None, description="Camera stream URL")
    location: Optional[str] = Field(None, description="Camera location")
    resolution: Optional[str] = Field(None, description="Resolution (e.g., 1920x1080)")


class CameraResponse(BaseModel):
    """Schema for camera responses."""
    id: int
    camera_id: str
    name: str
    module_id: int
    stream_url: str
    location: Optional[str]
    resolution: Optional[str]
    status: str
    last_seen: Optional[datetime]
    registered_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CameraStatusUpdate(BaseModel):
    """Schema for updating camera status."""
    status: str = Field(..., description="Camera status (online, offline, error)")


# ============================================================================
# Common Schemas
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[dict] = None
