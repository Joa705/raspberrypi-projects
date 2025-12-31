from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Project imports
from database.db import get_db
from database.models import Camera
import crud.camera as camera_crud

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/motion")
async def motion_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Webhook endpoint - camera POSTs here when motion/AI detection occurs"""
    
    # Get camera IP from the request
    camera_ip = request.client.host if request.client else "unknown"
    
    logger.info(f"📥 Webhook received from camera: {camera_ip}")

    try:
        camera = await camera_crud.get_camera_by_ip(db, camera_ip)
        
        if not camera:
            return {
                "status": "error",
                "message": f"Camera {camera_ip} not registered",
                "camera_ip": camera_ip
            }
        
        logger.info(f"✓ Camera found: {camera.name} (ID: {camera.camera_id})")
        
    except Exception as e:
        logger.error(f"❌ Database error checking camera: {e}", exc_info=True)
        return {
            "status": "error",
            "message": "Database error"
        }

    try:
        data = await request.json()
        
        # Extract alarm information
        alarm_data = data.get('alarm', {})
        alarm_type = alarm_data.get('type', 'UNKNOWN')
        device_name = alarm_data.get('channelName', 'Unknown')
        channel = alarm_data.get('channel', 0)
        alarm_time = alarm_data.get('alarmTime', '')
        message = alarm_data.get('message', '')
        
        # Map alarm types to emojis and descriptions
        alarm_types = {
            'MD': ('🚨', 'Motion Detection'),
            'PEOPLE': ('👤', 'Person Detected'),
            'VEHICLE': ('🚗', 'Vehicle Detected'),
            'PET': ('🐾', 'Pet Detected'),
            'FACE': ('😊', 'Face Detected'),
            'LP': ('🔋', 'Low Battery'),
            'visitor': ('🔔', 'Doorbell Press'),
        }
        
        emoji, description = alarm_types.get(alarm_type, ('⚠️', 'Unknown Event'))
        logger.info(f"{emoji} {description} on '{device_name}' (Channel {channel}) at {alarm_time}")
        
        # TODO: Add your actions here based on event type
        if alarm_type == 'PEOPLE':
            pass
            # await start_recording(channel)
            # await save_to_database(alarm_data)
            # await send_push_notification(f"Person detected in {device_name}")
            
        elif alarm_type == 'MD':
            pass
            # await start_recording(channel)
            
        elif alarm_type == 'VEHICLE':
            pass
            # await log_vehicle_event(alarm_data)
            
        elif alarm_type == 'LP':
            pass
            # await send_battery_alert(device_name)
        
        return {
            "status": "ok",
            "message": f"{description} event received",
            "alarm_type": alarm_type,
            "device": device_name
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }