"""
Camera Controller Module

This module provides high-level camera control logic for managing
multiple Tapo camera RTSP streams with viewer-based lifecycle management.

Features:
- Manages multiple camera streams simultaneously
- Lazy initialization: streams start only when first viewer connects
- Automatic cleanup: streams stop when last viewer disconnects
- Singleton pattern: multiple viewers share the same stream instance
- Thread-safe viewer counting
"""

import logging
import threading
import time
import cv2
from typing import Dict, Optional
from queue import Queue, Empty

from .config import get_camera_config, camera_exists

logger = logging.getLogger(__name__)


class CameraStream:
    """
    Manages a single camera RTSP stream with multiple viewers.
    
    The stream starts when the first viewer connects and stops
    when the last viewer disconnects.
    """
    
    def __init__(self, camera_id: str):
        """Initialize camera stream manager"""
        self.camera_id = camera_id
        self.config = get_camera_config(camera_id)
        
        # RTSP URL construction
        self.rtsp_url = (
            f"rtsp://{self.config.username}:{self.config.password}"
            f"@{self.config.ip_address}:554/{self.config.stream_quality}"
        )
        
        # Stream state
        self.capture: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.viewer_count = 0
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        
        # Frame buffer for viewers
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        logger.info(f"Camera stream manager created for {camera_id}")
    
    def add_viewer(self) -> bool:
        """
        Add a viewer to this stream. Starts the stream if this is the first viewer.
        Returns True if successful.
        """
        with self.lock:
            self.viewer_count += 1
            logger.info(f"Camera {self.camera_id}: Viewer added (total: {self.viewer_count})")
            
            if self.viewer_count == 1 and not self.is_running:
                # First viewer - start the stream
                return self._start_stream()
            
            return self.is_running
    
    def remove_viewer(self):
        """
        Remove a viewer from this stream. Stops the stream if this was the last viewer.
        """
        with self.lock:
            self.viewer_count = max(0, self.viewer_count - 1)
            logger.info(f"Camera {self.camera_id}: Viewer removed (remaining: {self.viewer_count})")
            
            if self.viewer_count == 0 and self.is_running:
                # Last viewer disconnected - stop the stream
                self._stop_stream()
    
    def _start_stream(self) -> bool:
        """Start the camera stream (internal method, assumes lock is held)"""
        if self.is_running:
            return True
        
        try:
            logger.info(f"Camera {self.camera_id}: Starting RTSP stream from {self.config.ip_address}")
            
            # Initialize OpenCV capture
            self.capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            
            # Aggressive latency reduction settings - disable buffering completely
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 0)  # No buffering for real-time
            self.capture.set(cv2.CAP_PROP_FPS, 15)  # Limit to 15 FPS
            self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            
            # Test connection
            ret, frame = self.capture.read()
            if not ret:
                raise Exception("Failed to read initial frame from camera")
            
            self.is_running = True
            
            # Start capture thread
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            
            logger.info(f"Camera {self.camera_id}: Stream started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Camera {self.camera_id}: Failed to start stream: {e}")
            if self.capture:
                self.capture.release()
                self.capture = None
            return False
    
    def _stop_stream(self):
        """Stop the camera stream (internal method, assumes lock is held)"""
        if not self.is_running:
            return
        
        logger.info(f"Camera {self.camera_id}: Stopping stream")
        self.is_running = False
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        # Release capture
        if self.capture:
            self.capture.release()
            self.capture = None
        
        # Clear frame buffer
        with self.frame_lock:
            self.current_frame = None
        
        logger.info(f"Camera {self.camera_id}: Stream stopped")
    
    def _capture_loop(self):
        """
        Continuous capture loop that runs in a separate thread.
        Aggressively skips old buffered frames to maintain real-time streaming.
        """
        error_count = 0
        max_errors = 10
        
        logger.info(f"Camera {self.camera_id}: Capture loop started")
        
        while self.is_running:
            try:
                if not self.capture or not self.capture.isOpened():
                    logger.warning(f"Camera {self.camera_id}: Capture not opened, reconnecting...")
                    time.sleep(2)
                    continue
                
                # Flush old buffered frames by grabbing without retrieving
                # This discards old frames to get the latest one
                for _ in range(3):  # Skip up to 3 buffered frames
                    self.capture.grab()
                
                # Now retrieve the latest frame after flushing buffer
                ret, frame = self.capture.retrieve()
                
                if not ret:
                    error_count += 1
                    if error_count >= max_errors:
                        logger.error(f"Camera {self.camera_id}: Too many read errors, attempting reconnect")
                        self.capture.release()
                        time.sleep(2)
                        self.capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 0)  # No buffering
                        self.capture.set(cv2.CAP_PROP_FPS, 15)
                        error_count = 0
                    time.sleep(0.01)
                    continue
                
                # Successfully read frame
                error_count = 0
                
                # Update shared frame buffer with latest frame
                with self.frame_lock:
                    self.current_frame = frame
                
                # Minimal delay for fast frame capture
                time.sleep(0.033)  # ~30 FPS capture rate
                
            except Exception as e:
                logger.error(f"Camera {self.camera_id}: Error in capture loop: {e}")
                error_count += 1
                time.sleep(0.1)
        
        logger.info(f"Camera {self.camera_id}: Capture loop ended")
    
    def get_frame(self) -> Optional[bytes]:
        """
        Get the current frame as JPEG bytes.
        Returns None if no frame is available.
        """
        with self.frame_lock:
            if self.current_frame is None:
                return None
            
            # Encode frame as JPEG with lower quality for faster encoding
            ret, buffer = cv2.imencode('.jpg', self.current_frame, 
                                      [cv2.IMWRITE_JPEG_QUALITY, 50])
            if not ret:
                return None
            
            return buffer.tobytes()
    
    def get_status(self) -> dict:
        """Get current stream status"""
        with self.lock:
            return {
                "camera_id": self.camera_id,
                "camera_name": self.config.name,
                "is_running": self.is_running,
                "viewer_count": self.viewer_count,
                "ip_address": self.config.ip_address
            }


class CameraController:
    """
    Central controller for managing multiple camera streams.
    
    Maintains a singleton instance of each camera stream and manages
    their lifecycle based on viewer connections.
    """
    
    def __init__(self):
        """Initialize the camera controller"""
        self.streams: Dict[str, CameraStream] = {}
        self.lock = threading.Lock()
        logger.info("Camera controller initialized")
    
    def get_stream(self, camera_id: str) -> Optional[CameraStream]:
        """
        Get or create a stream for the specified camera.
        Returns None if the camera doesn't exist in configuration.
        """
        if not camera_exists(camera_id):
            logger.warning(f"Camera {camera_id} not found in configuration")
            return None
        
        with self.lock:
            if camera_id not in self.streams:
                # Create new stream manager
                self.streams[camera_id] = CameraStream(camera_id)
            
            return self.streams[camera_id]
    
    def cleanup_inactive_streams(self):
        """
        Remove stream instances that are not running and have no viewers.
        This is called periodically to free resources.
        """
        with self.lock:
            to_remove = []
            for camera_id, stream in self.streams.items():
                if not stream.is_running and stream.viewer_count == 0:
                    to_remove.append(camera_id)
            
            for camera_id in to_remove:
                logger.info(f"Removing inactive stream: {camera_id}")
                del self.streams[camera_id]
    
    def get_all_status(self) -> dict:
        """Get status of all active streams"""
        with self.lock:
            return {
                camera_id: stream.get_status()
                for camera_id, stream in self.streams.items()
            }
    
    def shutdown(self):
        """Shutdown all streams"""
        logger.info("Shutting down camera controller")
        with self.lock:
            for stream in self.streams.values():
                stream._stop_stream()
            self.streams.clear()


# Global controller instance
_controller: Optional[CameraController] = None
_controller_lock = threading.Lock()


def get_camera_controller() -> CameraController:
    """Get the global camera controller instance (singleton)"""
    global _controller
    
    if _controller is None:
        with _controller_lock:
            if _controller is None:
                _controller = CameraController()
    
    return _controller
