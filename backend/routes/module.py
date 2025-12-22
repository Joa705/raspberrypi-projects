"""
Module API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging

from database.db import get_db
from database.models import Module
from models.schemas import ModuleRegister, ModuleResponse, ModuleStatusUpdate, SuccessResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=SuccessResponse, status_code=201)
async def register_module(
    data: ModuleRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new module."""
    try:
        # Check if module already exists
        query = select(Module).where(Module.module_id == data.module_id)
        result = await db.execute(query)
        existing_module = result.scalar_one_or_none()
        
        if existing_module:
            raise HTTPException(
                status_code=400,
                detail=f"Module {data.module_id} already registered"
            )
        
        # Create new module
        module = Module(
            module_id=data.module_id,
            module_type=data.module_type,
            name=data.name,
            description=data.description,
            url=data.url,
            status="online",
            last_seen=datetime.now()
        )
        
        db.add(module)
        await db.commit()
        await db.refresh(module)
        
        logger.info(f"Module registered: {data.module_id} (type: {data.module_type})")
        return SuccessResponse(
            message="Module registered successfully",
            data={"module_id": data.module_id, "id": module.id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering module: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{module_id}/status", response_model=SuccessResponse)
async def update_module_status(
    module_id: str,
    data: ModuleStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update module status (heartbeat endpoint)."""
    try:
        query = select(Module).where(Module.module_id == module_id)
        result = await db.execute(query)
        module = result.scalar_one_or_none()
        
        if not module:
            raise HTTPException(status_code=404, detail=f"Module {module_id} not found")
        
        module.status = data.status
        module.last_seen = datetime.now()
        
        await db.commit()
        
        logger.debug(f"Updated status for module {module_id}: {data.status}")
        
        return SuccessResponse(
            message="Module status updated",
            data={"module_id": module_id, "status": data.status}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating module status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
