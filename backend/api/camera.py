"""
Camera API Routes

This module defines FastAPI routes for camera operations.
Provides endpoints for streaming from multiple Tapo cameras.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging
import time
import asyncio

# Import models
from models.camera import CameraBase, CameraCreateRequest, CameraCreateResponse

# Import camera controller
from database.crud_camera import db_get_camera, db_get_cameras, db_create_camera
from database.db import get_db
from modules.camera.controller import get_camera_controller

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter()


async def generate_stream(camera_id: int, request: Request, camera_data: CameraBase):
    """
    Generator function that yields MJPEG frames for a specific camera.
    Manages viewer lifecycle for the stream.
    """
    controller = get_camera_controller()
    
    stream = controller.get_stream(camera_id, camera_data)
    
    if stream is None:
        logger.error(f"Camera {camera_id} not found")
        return
    
    # Add this viewer to the stream
    if not stream.add_viewer():
        logger.error(f"Failed to start stream for camera {camera_id}")
        return
    
    try:
        logger.info(f"Starting stream for viewer on camera {camera_id}")
        
        # Wait for first frame to be available (up to 5 seconds)
        retries = 0
        while stream.is_running and stream.get_frame() is None and retries < 50:
            await asyncio.sleep(0.1)
            retries += 1
        
        last_frame = None
        frames_sent = 0
        
        # Stream frames to the client
        while stream.is_running:
            # Check if client is still connected
            if await request.is_disconnected():
                logger.info(f"Camera {camera_id}: Client disconnected (detected by request)")
                break
            
            frame_bytes = stream.get_frame()
            
            if frame_bytes is None:
                # No new frame, wait a bit
                await asyncio.sleep(0.01)
                continue
            
            # Only send if frame changed (reduces redundant sends)
            if frame_bytes != last_frame:
                last_frame = frame_bytes
                frames_sent += 1
                
                # Yield frame in MJPEG format
                try:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                except Exception as e:
                    # Connection broken
                    logger.info(f"Camera {camera_id}: Connection broken after {frames_sent} frames: {e}")
                    break
            
            # Small delay to prevent overwhelming the connection
            await asyncio.sleep(0.033)  # ~30 FPS
    
    except GeneratorExit:
        # Client disconnected
        logger.info(f"Client disconnected from camera {camera_id}")
    
    except Exception as e:
        logger.error(f"Error streaming camera {camera_id}: {e}")
    
    finally:
        # Remove this viewer from the stream
        stream.remove_viewer()
        logger.info(f"Viewer removed from camera {camera_id}")


@router.get("/{camera_id}/stream")
async def camera_stream(camera_id: int, request: Request, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    """
    Stream live video from a specific camera.
    
    The stream starts automatically when the first viewer connects
    and stops when the last viewer disconnects.
    
    Args:
        camera_id: ID of the camera to stream from
        request: FastAPI request object for disconnect detection
    
    Returns:
        StreamingResponse with MJPEG video stream
    """
    
    db_camera = await db_get_camera(db, camera_id)
    # Check if camera exists
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found") 
    
    camera_data = CameraBase.model_validate(db_camera, from_attributes=True)

    # Return streaming response
    return StreamingResponse(
        generate_stream(camera_id, request, camera_data),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/{camera_id}/status")
async def camera_status(camera_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Get the current status of a specific camera.
    
    Args:
        camera_id: ID of the camera
    
    Returns:
        Camera status including viewer count and stream state
    """
    
    db_camera = await db_get_camera(db, camera_id)
    # Check if camera exists
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found") 
    
    # Validate database camera object to Pydantic model
    camera_data = CameraBase.model_validate(db_camera, from_attributes=True)
    
    controller = get_camera_controller()
    stream = controller.get_stream(camera_id, camera_data)
    
    if stream:
        return stream.get_status()
    else:
        # Camera exists but stream not yet created
        return {
            "camera_id": camera_id,
            "camera_name": camera_data.name,
            "is_running": False,
            "viewer_count": 0,
            "ip_address": camera_data.ip_address
        }


@router.get("s")
async def list_cameras(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    List all configured cameras and their current status.
    
    Returns:
        Dictionary with camera IDs and their status
    """
    controller = get_camera_controller()
    db_cameras = await db_get_cameras(db)

    
    cameras = {}
    for camera in db_cameras:
        camera_data = CameraBase.model_validate(camera, from_attributes=True)
        stream = controller.get_stream(camera.camera_id, camera_data)
        
        if stream:
            cameras[camera.camera_id] = stream.get_status()
        else:
            cameras[camera.camera_id] = {
                "camera_id": camera.camera_id,
                "camera_name": camera_data.name,
                "is_running": False,
                "viewer_count": 0,
                "ip_address": camera_data.ip_address
            }
    
    return {
        "cameras": cameras,
        "total_count": len(cameras)
    }


@router.post("/{camera_id}/cleanup")
async def cleanup_camera(camera_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """
    Force cleanup of a camera stream (for administrative use).
    
    This will stop the stream regardless of viewer count.
    
    Args:
        camera_id: ID of the camera to cleanup
    
    Returns:
        Status message
    """
    db_camera = await db_get_camera(db, camera_id)
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    camera_data = CameraBase.model_validate(db_camera, from_attributes=True)

    controller = get_camera_controller()
    stream = controller.get_stream(camera_id, camera_data)
    
    if stream and stream.is_running:
        stream._stop_stream()
        return {"status": "success", "message": f"Camera {camera_id} stream stopped"}
    else:
        return {"status": "success", "message": f"Camera {camera_id} was not running"}


@router.post("/create", response_model=CameraCreateResponse, status_code=201)
async def create_camera(
    camera: CameraCreateRequest, 
    db: AsyncSession = Depends(get_db)
) -> CameraCreateResponse:
    """
    Create a new camera configuration.
    
    Args:
        camera: CameraCreateRequest model with camera details
        db: Async database session
    
    Returns:
        CameraCreateResponse: Created camera with database-generated fields
    """
    new_camera = await db_create_camera(db, camera)
    if not new_camera:
        raise HTTPException(status_code=500, detail="Failed to create camera")
    
    return CameraCreateResponse.model_validate(new_camera, from_attributes=True)