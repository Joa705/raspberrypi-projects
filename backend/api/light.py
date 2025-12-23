"""
Light Control API Routes

This module defines FastAPI routes for light control operations.
It imports and uses the light relay hardware module but contains no hardware logic itself.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

# Import light relay hardware module
from modules.light import LightRelay

# Import models
from models.light import LightResponse, LightStatusResponse

# Create API router
router = APIRouter()

# Create a single light relay instance
light_relay = LightRelay()


@router.post(
    "/on",
    response_model=LightResponse,
    responses={
        200: {"description": "Light turned on successfully"},
        500: {"description": "Failed to turn light on"}
    }
)
async def turn_light_on():
    """
    Turn the light on.
    
    Activates the relay to turn the connected light on. If already on,
    the operation completes successfully with no state change.
    
    Returns:
        Status confirmation with current light state
    """
    try:
        success = light_relay.turn_on()
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to turn light on"
            )
        
        return LightResponse(
            status="success",
            message="Light turned on",
            is_on=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error turning light on: {str(e)}"
        )


@router.post(
    "/off",
    response_model=LightResponse,
    responses={
        200: {"description": "Light turned off successfully"},
        500: {"description": "Failed to turn light off"}
    }
)
async def turn_light_off():
    """
    Turn the light off.
    
    Deactivates the relay to turn the connected light off. If already off,
    the operation completes successfully with no state change.
    
    Returns:
        Status confirmation with current light state
    """
    try:
        success = light_relay.turn_off()
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to turn light off"
            )
        
        return LightResponse(
            status="success",
            message="Light turned off",
            is_on=False
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error turning light off: {str(e)}"
        )


@router.post(
    "/toggle",
    response_model=LightResponse,
    responses={
        200: {"description": "Light toggled successfully"},
        500: {"description": "Failed to toggle light"}
    }
)
async def toggle_light():
    """
    Toggle the light state.
    
    Switches the light to the opposite state: if currently on, turns it off,
    and vice versa. Useful for simple on/off switching without needing to
    know the current state.
    
    Returns:
        Status confirmation with new light state
    """
    try:
        success = light_relay.toggle()
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to toggle light"
            )
        
        status = light_relay.get_status()
        
        return LightResponse(
            status="success",
            message=f"Light toggled {'on' if status['is_on'] else 'off'}",
            is_on=status['is_on']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error toggling light: {str(e)}"
        )


@router.get("/status")
async def get_light_status():
    """
    GET /light/status
    
    Get the current light status.
    
    Returns:
        Dict: Light status information
    """
    try:
        status = light_relay.get_status()
        
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
            detail=f"Error getting light status: {str(e)}"
        )
