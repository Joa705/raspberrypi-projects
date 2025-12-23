"""
Light Control Models

Pydantic models for light control API request/response validation.
"""

from pydantic import BaseModel, Field


class LightResponse(BaseModel):
    """Response model for light control operations"""
    status: str = Field(..., description="Operation status", example="success")
    message: str = Field(..., description="Human-readable status message", example="Light turned on")
    is_on: bool = Field(..., description="Current light state", example=True)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Light turned on",
                "is_on": True
            }
        }


class LightStatusResponse(BaseModel):
    """Response model for light status"""
    initialized: bool = Field(..., description="Whether relay is initialized", example=True)
    is_on: bool = Field(..., description="Current light state", example=False)
    gpio_pin: int = Field(..., description="GPIO pin number", example=17)

    class Config:
        json_schema_extra = {
            "example": {
                "initialized": True,
                "is_on": False,
                "gpio_pin": 17
            }
        }
