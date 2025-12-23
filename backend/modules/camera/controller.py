"""
Camera Controller Module

This module provides high-level camera control logic.
It orchestrates the camera driver and provides business logic
for camera operations.
"""

from typing import Optional, Dict
from .driver import CameraDriver


class CameraController:
    """
    High-level camera controller.
    
    Provides business logic for camera operations and manages
    the camera driver lifecycle.
    """
    
    def __init__(self):
        self.driver = CameraDriver()
        self.is_streaming = False
        self._initialize()
    
    def _initialize(self):
        """
        Initialize the camera controller and driver.
        """
        self.driver.initialize()
    
    def get_snapshot(self) -> Optional[Dict]:
        """
        Capture a single snapshot from the camera.
        
        Returns:
            Optional[Dict]: Dictionary containing snapshot data and metadata,
                          or None if capture failed
        """
        image_data = self.driver.capture_image()
        
        if image_data is None:
            return None
        
        return {
            "status": "success",
            "image_data": image_data.decode() if isinstance(image_data, bytes) else image_data,
            "format": "mock",
            "timestamp": self._get_timestamp()
        }
    
    def start_streaming(self) -> Dict:
        """
        Start camera streaming.
        
        Returns:
            Dict: Status dictionary with success/failure information
        """
        if self.is_streaming:
            return {
                "status": "already_streaming",
                "message": "Camera is already streaming"
            }
        
        success = self.driver.start_stream()
        
        if success:
            self.is_streaming = True
            return {
                "status": "success",
                "message": "Camera streaming started"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to start camera streaming"
            }
    
    def stop_streaming(self) -> Dict:
        """
        Stop camera streaming.
        
        Returns:
            Dict: Status dictionary with success/failure information
        """
        if not self.is_streaming:
            return {
                "status": "not_streaming",
                "message": "Camera is not currently streaming"
            }
        
        success = self.driver.stop_stream()
        
        if success:
            self.is_streaming = False
            return {
                "status": "success",
                "message": "Camera streaming stopped"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to stop camera streaming"
            }
    
    def get_status(self) -> Dict:
        """
        Get current camera status.
        
        Returns:
            Dict: Camera status information
        """
        return {
            "initialized": self.driver.is_initialized,
            "streaming": self.is_streaming,
            "active": self.driver.camera_active
        }
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp.
        
        Returns:
            str: ISO format timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def cleanup(self):
        """
        Clean up camera resources.
        """
        if self.is_streaming:
            self.stop_streaming()
        self.driver.cleanup()
