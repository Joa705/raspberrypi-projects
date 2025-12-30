"""
Camera Models

Pydantic models for camera API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class CameraType(str, Enum):
    """Supported camera types/brands"""
    REOLINK = "reolink"
    TAPO = "tapo"
    GENERIC = "generic"

class StreamQuality(str, Enum):
    """Supported stream quality options"""
    HD = "hd"
    SD = "sd"
    
    
class CameraBase(BaseModel):
    """Base camera model with common fields"""
    name: str = Field(..., description="Camera display name", example="Living Room Camera")
    ip_address: str = Field(..., description="Camera IP address", example="10.0.0.24")
    username: str = Field(..., description="Camera authentication username")
    password: str = Field(..., description="Camera authentication password")
    stream_quality: StreamQuality = Field(default=StreamQuality.SD, description="Stream quality (HD or SD)", example="SD")
    description: str = Field(default="", description="Camera description", example="Main living room camera")
    camera_type: CameraType = Field(default=CameraType.REOLINK, description="Type/brand of the camera", example="reolink")


class CameraResponse(CameraBase):
    """Model for camera response from database"""
    camera_id: int = Field(..., description="Auto-generated camera identifier", example=1)
    created_at: datetime = Field(..., description="Camera creation timestamp")
    updated_at: datetime = Field(..., description="Camera last update timestamp")
    
    class Config:
        from_attributes = True
        

class CameraStreamConfig(CameraBase):
    """Model for camera stream configuration -- used internally by controller"""
    camera_id: int = Field(..., description="Camera identifier", example=1)

    class Config:
        from_attributes = True
        
    
class CameraCreateRequest(CameraBase):
    """Model for creating a new camera"""
    pass  # Inherits all fields from CameraBase


class CameraUpdate(BaseModel):
    """Model for updating a camera - all fields optional"""
    name: Optional[str] = None
    ip_address: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    stream_quality: Optional[str] = None
    description: Optional[str] = None
        
        
class CameraRuntimeStatus(BaseModel):
    """Runtime state from CameraStream (in-memory only)"""
    camera_id: int
    is_running: bool
    viewer_count: int
    stream_type: str = "webrtc"  # "webrtc" or "hls" 
    uptime_seconds: Optional[int] = None
    peer_connection_count: int = 0  # Active WebRTC connections


class CameraWithStatus(CameraResponse):
    """Combined: static config + runtime status"""
    status: CameraRuntimeStatus


class WebRTCOffer(BaseModel):
    """WebRTC offer from client"""
    sdp: str = Field(..., description="Session Description Protocol offer")
    type: str = Field(..., description="SDP type", example="offer")

class WebRTCAnswer(BaseModel):
    """WebRTC answer from server"""
    sdp: str = Field(..., description="Session Description Protocol answer")
    type: str = Field(..., description="SDP type", example="answer")