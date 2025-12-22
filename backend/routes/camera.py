"""
Camera API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import logging

from database.db import get_db
from database.models import Camera, Module
from models.schemas import CameraRegister, CameraResponse, CameraStatusUpdate, SuccessResponse
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=SuccessResponse, status_code=201)
async def register_camera(
    data: CameraRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new camera."""
    try:
        # Check if camera already exists
        query = select(Camera).where(Camera.camera_id == data.camera_id)
        result = await db.execute(query)
        existing_camera = result.scalar_one_or_none()
        
        if existing_camera:
            raise HTTPException(
                status_code=400,
                detail=f"Camera {data.camera_id} already registered"
            )
        
        # Verify module exists
        module_query = select(Module).where(Module.module_id == data.module_id)
        module_result = await db.execute(module_query)
        module = module_result.scalar_one_or_none()
        
        if not module:
            raise HTTPException(
                status_code=404,
                detail=f"Module {data.module_id} not found"
            )
        
        # Create new camera
        camera = Camera(
            camera_id=data.camera_id,
            name=data.name,
            module_id=data.module_id,  # Use UUID directly
            stream_url=data.stream_url,
            location=data.location,
            resolution=data.resolution,
            status="online"
        )
        
        db.add(camera)
        await db.commit()
        await db.refresh(camera)
        
        logger.info(f"Camera registered: {data.camera_id}")
        return SuccessResponse(
            message="Camera registered successfully",
            data={"camera_id": str(data.camera_id)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    module_id: Optional[UUID] = Query(None, description="Filter by module UUID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """List all registered cameras."""
    try:
        query = select(Camera)
        
        if module_id:
            query = query.where(Camera.module_id == module_id)
        
        if status:
            query = query.where(Camera.status == status)
        
        query = query.order_by(desc(Camera.registered_at))
        
        result = await db.execute(query)
        cameras = result.scalars().all()
        
        return cameras
        
    except Exception as e:
        logger.error(f"Error listing cameras: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get details for a specific camera."""
    try:
        query = select(Camera).where(Camera.camera_id == camera_id)
        result = await db.execute(query)
        camera = result.scalar_one_or_none()
        
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        return camera
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{camera_id}/status", response_model=SuccessResponse)
async def update_camera_status(
    camera_id: UUID,
    data: CameraStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update camera status (heartbeat endpoint)."""
    try:
        query = select(Camera).where(Camera.camera_id == camera_id)
        result = await db.execute(query)
        camera = result.scalar_one_or_none()
        
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        camera.status = data.status
        camera.last_seen = datetime.now()
        
        await db.commit()
        
        logger.debug(f"Updated status for camera {camera_id}: {data.status}")
        
        return SuccessResponse(
            message="Camera status updated",
            data={"camera_id": camera_id, "status": data.status}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating camera status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{camera_id}", response_model=SuccessResponse)
async def update_camera(
    camera_id: UUID,
    stream_url: Optional[str] = None,
    location: Optional[str] = None,
    resolution: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Update camera details."""
    try:
        query = select(Camera).where(Camera.camera_id == camera_id)
        result = await db.execute(query)
        camera = result.scalar_one_or_none()
        
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        # Update fields if provided
        if stream_url is not None:
            camera.stream_url = stream_url
        if location is not None:
            camera.location = location
        if resolution is not None:
            camera.resolution = resolution
        
        camera.last_seen = datetime.now()
        
        await db.commit()
        
        logger.info(f"Updated camera {camera_id}")
        
        return SuccessResponse(
            message="Camera updated successfully",
            data={"camera_id": camera_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{camera_id}", response_model=SuccessResponse)
async def delete_camera(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a camera."""
    try:
        query = select(Camera).where(Camera.camera_id == camera_id)
        result = await db.execute(query)
        camera = result.scalar_one_or_none()
        
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
        
        await db.delete(camera)
        await db.commit()
        
        logger.info(f"Deleted camera {camera_id}")
        
        return SuccessResponse(
            message="Camera deleted successfully",
            data={"camera_id": camera_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))