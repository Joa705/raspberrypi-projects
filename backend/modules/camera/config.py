"""
Camera Configuration

Define all available Tapo cameras with their RTSP connection details.
Add or modify cameras here to configure the system.
"""

from typing import Dict, List
from pydantic import BaseModel


class CameraConfig(BaseModel):
    """Configuration for a single Tapo camera"""
    camera_id: str
    name: str
    ip_address: str
    username: str
    password: str
    stream_quality: str = "stream1"  # stream1 = HD (1920x1080), stream2 = SD (640x360)
    description: str = ""


# Define your cameras here
CAMERAS: Dict[str, CameraConfig] = {
    "cam1": CameraConfig(
        camera_id="cam1",
        name="Living Room Camera",
        ip_address="10.0.0.24",
        username="joachim",
        password="hemmelig",
        stream_quality="stream2",
        description="Main living room camera"
    ),
        "cam2": CameraConfig(
        camera_id="cam2",
        name="Outdoor Camera",
        ip_address="10.0.0.102",
        username="sveinorjan",
        password="hemmelig",
        stream_quality="stream2",
        description="Outdoor camera"
    ),
        "cam3": CameraConfig(
        camera_id="cam3",
        name="Bua Camera",
        ip_address="10.0.0.11",
        username="sveinorjan",
        password="hemmelig",
        stream_quality="stream2",
        description="Bua"
    ),
    # Add more cameras as needed:
    # "cam2": CameraConfig(
    #     camera_id="cam2",
    #     name="Bedroom Camera",
    #     ip_address="10.0.0.25",
    #     username="joachim",
    #     password="hemmelig",
    #     stream_quality="stream2",
    #     description="Bedroom monitoring"
    # ),
}


def get_camera_config(camera_id: str) -> CameraConfig:
    """Get configuration for a specific camera"""
    if camera_id not in CAMERAS:
        raise ValueError(f"Camera {camera_id} not found in configuration")
    return CAMERAS[camera_id]


def get_all_camera_ids() -> List[str]:
    """Get list of all configured camera IDs"""
    return list(CAMERAS.keys())


def camera_exists(camera_id: str) -> bool:
    """Check if a camera exists in configuration"""
    return camera_id in CAMERAS
