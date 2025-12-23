"""
Camera API Routes

This module defines FastAPI routes for camera operations.
Provides endpoints for streaming from multiple Tapo cameras.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any
import logging
import time
import asyncio

# Import models
from models.camera import CameraStatusResponse

# Import camera controller
from modules.camera.controller import get_camera_controller
from modules.camera.config import get_all_camera_ids, camera_exists, get_camera_config

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter()


async def generate_stream(camera_id: str, request: Request):
    """
    Generator function that yields MJPEG frames for a specific camera.
    Manages viewer lifecycle for the stream.
    """
    controller = get_camera_controller()
    stream = controller.get_stream(camera_id)
    
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
async def camera_stream(camera_id: str, request: Request):
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
    # Check if camera exists
    if not camera_exists(camera_id):
        raise HTTPException(
            status_code=404,
            detail=f"Camera '{camera_id}' not found in configuration"
        )
    
    # Return streaming response
    return StreamingResponse(
        generate_stream(camera_id, request),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/{camera_id}/status")
async def camera_status(camera_id: str) -> Dict[str, Any]:
    """
    Get the current status of a specific camera.
    
    Args:
        camera_id: ID of the camera
    
    Returns:
        Camera status including viewer count and stream state
    """
    if not camera_exists(camera_id):
        raise HTTPException(
            status_code=404,
            detail=f"Camera '{camera_id}' not found in configuration"
        )
    
    controller = get_camera_controller()
    stream = controller.get_stream(camera_id)
    
    if stream:
        return stream.get_status()
    else:
        # Camera exists in config but stream not yet created
        config = get_camera_config(camera_id)
        return {
            "camera_id": camera_id,
            "camera_name": config.name,
            "is_running": False,
            "viewer_count": 0,
            "ip_address": config.ip_address
        }


@router.get("s")
async def list_cameras() -> Dict[str, Any]:
    """
    List all configured cameras and their current status.
    
    Returns:
        Dictionary with camera IDs and their status
    """
    controller = get_camera_controller()
    camera_ids = get_all_camera_ids()
    
    cameras = {}
    for camera_id in camera_ids:
        config = get_camera_config(camera_id)
        stream = controller.get_stream(camera_id)
        
        if stream:
            cameras[camera_id] = stream.get_status()
        else:
            cameras[camera_id] = {
                "camera_id": camera_id,
                "camera_name": config.name,
                "is_running": False,
                "viewer_count": 0,
                "ip_address": config.ip_address
            }
    
    return {
        "cameras": cameras,
        "total_count": len(cameras)
    }


@router.post("/{camera_id}/cleanup")
async def cleanup_camera(camera_id: str) -> Dict[str, str]:
    """
    Force cleanup of a camera stream (for administrative use).
    
    This will stop the stream regardless of viewer count.
    
    Args:
        camera_id: ID of the camera to cleanup
    
    Returns:
        Status message
    """
    if not camera_exists(camera_id):
        raise HTTPException(
            status_code=404,
            detail=f"Camera '{camera_id}' not found in configuration"
        )
    
    controller = get_camera_controller()
    stream = controller.get_stream(camera_id)
    
    if stream and stream.is_running:
        stream._stop_stream()
        return {"status": "success", "message": f"Camera {camera_id} stream stopped"}
    else:
        return {"status": "success", "message": f"Camera {camera_id} was not running"}


