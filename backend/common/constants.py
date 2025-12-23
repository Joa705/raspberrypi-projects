"""
Constants used throughout the backend application.
"""

class ModuleType:
    """Module type constants."""
    CAMERA_MONITOR = "camera_monitor"
    SENSOR = "sensor"
    HEAT = "heat"
    LED = "led"
    constants = [CAMERA_MONITOR, SENSOR, HEAT, LED]


class ModuleStatus:
    """Module status constants."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    constants = [ONLINE, OFFLINE, ERROR]


class CameraStatus:
    """Camera status constants."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    constants = [ONLINE, OFFLINE, ERROR]