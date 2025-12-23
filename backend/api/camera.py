"""
Camera API Routes

This module defines FastAPI routes for camera operations.
It imports and uses the camera hardware module but contains no hardware logic itself.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

# Import camera hardware module
from modules.camera import CameraController

# Create API router
router = APIRouter()

# Create a single camera controller instance
camera_controller = CameraController()


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


@router.get(
    "/snapshot",
    response_model=None,
    responses={
        200: {
            "description": "Snapshot captured successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "image_data": "MOCK_IMAGE_DATA",
                        "format": "mock",
                        "timestamp": "2025-12-23T10:30:00.123456"
                    }
                }
            }
        },
        500: {"description": "Failed to capture snapshot"}
    }
)
async def get_snapshot():
    """
    Capture a single snapshot from the camera.
    
    This endpoint triggers the camera to capture a single image and returns
    the image data along with metadata. In mock mode, returns placeholder data.
    
    Returns:
        Snapshot data with timestamp and format information
    """
    try:
        snapshot = camera_controller.get_snapshot()
        
        if snapshot is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to capture snapshot"
            )
        
        return JSONResponse(
            status_code=200,
            content=snapshot
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error capturing snapshot: {str(e)}"
        )


@router.post(
    "/stream/start",
    response_model=CameraResponse,
    responses={
        200: {"description": "Stream started successfully or already streaming"},
        500: {"description": "Failed to start stream"}
    }
)
async def start_stream():
    """
    Start video streaming from the camera.
    
    Initiates continuous video streaming from the camera. If streaming is
    already active, returns an appropriate status message.
    
    Returns:
        Status message indicating whether streaming started successfully
    """
    try:
        result = camera_controller.start_streaming()
        
        return CameraResponse(
            status=result["status"],
            message=result["message"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting stream: {str(e)}"
        )


@router.post("/stream/stop")
async def stop_stream():
    """
    POST /camera/stream/stop
    
    Stop video streaming from the camera.
    
    Returns:
        CameraResponse: Status of the stream stop operation
    """
    try:
        result = camera_controller.stop_streaming()
        
        return CameraResponse(
            status=result["status"],
            message=result["message"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping stream: {str(e)}"
        )


@router.get("/status")
async def get_status():
    """
    GET /camera/status
    
    Get the current camera status.
    
    Returns:
        Dict: Camera status information
    """
    try:
        status = camera_controller.get_status()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": status
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting camera status: {str(e)}"
        )
