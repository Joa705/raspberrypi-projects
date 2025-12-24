"""
Camera API Routes

This module defines FastAPI routes for camera operations.
Provides endpoints for streaming from multiple Tapo cameras.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging
import time
import asyncio

# Import models
from models.camera import CameraBase, CameraCreateRequest, CameraCreateResponse

# Import camera controller
from database.crud_camera import db_get_camera, db_get_cameras, db_create_camera
from database.db import get_db, AsyncSessionLocal
from modules.camera.controller import get_camera_controller, CameraController

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter()


@router.websocket("/{camera_id}/ws")
async def camera_websocket(websocket: WebSocket, camera_id: int):
    """
    WebSocket endpoint for camera streaming.
    Provides reliable connection management and automatic cleanup.
    """
    stream = None
    viewer_added = False
    
    try:
        await websocket.accept()
        logger.info(f"Camera {camera_id}: WebSocket client connected")

        # Manually create database session for WebSocket
        async with AsyncSessionLocal() as db:
            db_camera = await db_get_camera(db, camera_id)
            if not db_camera:
                try:
                    await websocket.send_json({"error": "Camera not found"})
                    await websocket.close()
                except Exception:
                    pass
                return
                
            camera_data = CameraBase.model_validate(db_camera, from_attributes=True)
        
        controller = get_camera_controller()
        stream = controller.get_stream(camera_id, camera_data)
        
        if not stream or not stream.add_viewer():
            try:
                await websocket.send_json({"error": "Failed to start stream"})
                await websocket.close()
            except Exception:
                pass
            return
        
        viewer_added = True
        logger.info(f"Camera {camera_id}: Starting WebSocket stream")
        
        # Wait for first frame
        retries = 0
        while stream.is_running and stream.get_frame() is None and retries < 50:
            await asyncio.sleep(0.1)
            retries += 1
        
        last_frame = None
        frames_sent = 0
        disconnected = False
        
        # Stream frames with immediate disconnect detection
        while stream.is_running and not disconnected:
            frame_bytes = stream.get_frame()
            
            if frame_bytes and frame_bytes != last_frame:
                last_frame = frame_bytes
                frames_sent += 1
                                
                # Send frame - catch any send errors
                try:
                    await websocket.send_bytes(frame_bytes)
                except (WebSocketDisconnect, RuntimeError, ConnectionError):
                    logger.info(f"Camera {camera_id}: Client disconnected during send")
                    disconnected = True
                    break
                except Exception as e:
                    logger.warning(f"Camera {camera_id}: Unexpected send error: {type(e).__name__}")
                    disconnected = True
                    break
            
            # Check for disconnect with short timeout
            if not disconnected:
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=0.033)
                except asyncio.TimeoutError:
                    # Expected timeout - continue streaming
                    pass
                except (WebSocketDisconnect, RuntimeError, ConnectionError):
                    logger.info(f"Camera {camera_id}: Client disconnected during receive")
                    disconnected = True
                    break
                except Exception as e:
                    logger.warning(f"Camera {camera_id}: Unexpected receive error: {type(e).__name__}")
                    disconnected = True
                    break
    
    except WebSocketDisconnect:
        logger.info(f"Camera {camera_id}: WebSocket disconnect exception")
    
    except Exception as e:
        logger.error(f"Camera {camera_id}: WebSocket error: {e}", exc_info=True)
    
    finally:
        # Always cleanup, but only if viewer was added
        if viewer_added and stream:
            logger.info(f"Camera {camera_id} disconnected: Cleaning up WebSocket viewer")
            stream.remove_viewer()
        
        # Ensure WebSocket is closed
        try:
            await websocket.close()
        except Exception:
            pass


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