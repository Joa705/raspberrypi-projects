"""
CRUD operations for database camera models.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from database.models import Camera
from schemas.camera import CameraBase, CameraUpdate, CameraCreateRequest


async def get_camera(db: AsyncSession, camera_id: int) -> Optional[Camera]:
    """Get a camera by ID"""
    result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    return result.scalar_one_or_none()


async def get_cameras(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Camera]:
    """Get all cameras with pagination"""
    result = await db.execute(select(Camera).offset(skip).limit(limit))
    return result.scalars().all()


async def create_camera(db: AsyncSession, camera: CameraCreateRequest) -> Camera:
    """Create a new camera"""
    db_camera = Camera(**camera.model_dump())
    db.add(db_camera)
    await db.flush()
    await db.refresh(db_camera)
    return db_camera


async def update_camera(db: AsyncSession, camera_id: int, camera: CameraUpdate) -> Optional[Camera]:
    """Update an existing camera"""
    db_camera = await get_camera(db, camera_id)
    if not db_camera:
        return None
    
    update_data = camera.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_camera, field, value)
    
    await db.flush()
    await db.refresh(db_camera)
    return db_camera


async def delete_camera(db: AsyncSession, camera_id: int) -> bool:
    """Delete a camera"""
    db_camera = await get_camera(db, camera_id)
    if not db_camera:
        return False
    
    await db.delete(db_camera)
    await db.flush()
    return True