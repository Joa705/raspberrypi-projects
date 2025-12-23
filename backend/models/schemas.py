"""
Pydantic schemas for module and camera API.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID

from common.constants import ModuleType, ModuleStatus, CameraStatus


# ============================================================================
# Module Schemas
# ============================================================================

class ModuleRegister(BaseModel):
    """Schema for registering a new module."""
    module_id: UUID = Field(..., description="Unique module identifier (UUID)")
    module_type: str = Field(..., description="Module type (camera_monitor, sensor, heat, led)")
    name: str = Field(..., description="Module name")
    description: Optional[str] = Field(None, description="Module description")
    url: str = Field(..., description="Module service URL")
    
    @field_validator('module_type')
    @classmethod
    def validate_module_type(cls, v: str) -> str:
        valid_types = ModuleType.constants
        if v not in valid_types:
            raise ValueError(f"module_type must be one of: {', '.join(valid_types)}")
        return v


class ModuleResponse(BaseModel):
    """Schema for module responses."""
    module_id: UUID
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
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = ModuleStatus.constants
        if v not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v


# ============================================================================
# Camera Schemas
# ============================================================================

class CameraRegister(BaseModel):
    """Schema for registering a camera."""
    camera_id: UUID = Field(..., description="Unique camera identifier (UUID)")
    name: str = Field(..., description="Camera name")
    module_id: UUID = Field(..., description="UUID of the module managing this camera")
    stream_url: Optional[str] = Field(None, description="Camera stream URL")
    location: Optional[str] = Field(None, description="Camera location")
    resolution: Optional[str] = Field(None, description="Resolution (e.g., 1920x1080)")


class CameraResponse(BaseModel):
    """Schema for camera responses."""
    camera_id: UUID
    name: str
    module_id: UUID
    stream_url: Optional[str]
    location: Optional[str]
    resolution: Optional[str]
    status: str
    last_seen: Optional[datetime]
    registered_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CameraStatusUpdate(BaseModel):
    """Schema for updating camera status."""
    status: str = Field(..., description="Camera status (online, offline, error)")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = CameraStatus.constants
        if v not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v


# ============================================================================
# Common Schemas
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[dict] = None