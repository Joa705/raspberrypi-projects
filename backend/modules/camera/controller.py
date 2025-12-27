import threading
import subprocess
import logging
import time
from typing import Optional, List
from datetime import datetime
from aiortc.contrib.media import MediaPlayer

# Project imports
from schemas.camera import CameraStreamConfig, CameraRuntimeStatus

logger = logging.getLogger(__name__)


def build_rtsp_url(camera: CameraStreamConfig) -> str:
    """Construct RTSP URL from camera details"""
    return f"rtsp://{camera.username}:{camera.password}@{camera.ip_address}:554/{camera.stream_quality}"


class CameraStream:
    """Manages a single camera stream with WebRTC support"""
    
    def __init__(self, camera_config: CameraStreamConfig):
        # Static config
        self.camera_id = camera_config.camera_id
        self.name = camera_config.name
        self.ip_address = camera_config.ip_address
        self.username = camera_config.username
        self.password = camera_config.password
        self.stream_quality = camera_config.stream_quality
        
        self.rtsp_url = build_rtsp_url(camera_config)
        
        # Runtime state (in-memory)
        self.is_running = False
        self.viewer_count = 0
        self.peer_connections: List = []  # List of RTCPeerConnection
        self.media_player: Optional[MediaPlayer] = None  # MediaPlayer handles FFmpeg internally
        self.video_track = None  # MediaStreamTrack
        self.start_time: Optional[float] = None
        self.lock = threading.Lock()
        
        logger.info(f"Camera {self.camera_id} ({self.name}): CameraStream initialized")
    
    def _start_stream(self) -> bool:
        """Start stream using MediaPlayer (handles FFmpeg internally)"""
        if self.media_player is not None:
            logger.warning(f"Camera {self.camera_id}: Stream already running")
            return True
        
        try:
            logger.info(f"Camera {self.camera_id}: Starting stream from {self.rtsp_url}")
            
            # MediaPlayer handles FFmpeg internally - much simpler!
            self.media_player = MediaPlayer(
                self.rtsp_url,
                format='rtsp',
                options={
                    'rtsp_transport': 'udp',
                    'fflags': 'nobuffer',
                    'flags': 'low_delay',
                    'probesize': '32',
                    'analyzeduration': '0',
                    'max_delay': '500000',        # 500ms max delay (microseconds)
                    'reorder_queue_size': '0',    # Don't reorder packets
                    'buffer_size': '512000',      # Larger network buffer (512KB)
                }
            )
            
            # Get video track from MediaPlayer
            self.video_track = self.media_player.video
            
            self.is_running = True
            self.start_time = time.time()
            
            logger.info(f"Camera {self.camera_id}: Stream started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Camera {self.camera_id}: Failed to start stream: {e}")
            self.media_player = None
            self.video_track = None
            self.is_running = False
            return False
    
    def _stop_stream(self) -> bool:
        """Stop MediaPlayer stream"""
        if self.media_player is None:
            logger.debug(f"Camera {self.camera_id}: Stream not running")
            return True
        
        try:
            logger.info(f"Camera {self.camera_id}: Stopping stream")
            
            # Stop video track
            if self.video_track:
                self.video_track.stop()
                self.video_track = None
            
            # MediaPlayer cleanup is handled automatically
            self.media_player = None
            self.is_running = False
            self.start_time = None
            
            logger.info(f"Camera {self.camera_id}: Stream stopped")
            return True
            
        except Exception as e:
            logger.error(f"Camera {self.camera_id}: Error stopping stream: {e}")
            return False
    
    def add_peer_connection(self, pc) -> None:
        """Add a WebRTC peer connection"""
        with self.lock:
            self.peer_connections.append(pc)
            logger.info(f"Camera {self.camera_id}: Added peer connection (total: {len(self.peer_connections)})")
    
    def remove_peer_connection(self, pc) -> None:
        """Remove a WebRTC peer connection"""
        with self.lock:
            if pc in self.peer_connections:
                self.peer_connections.remove(pc)
                logger.info(f"Camera {self.camera_id}: Removed peer connection (total: {len(self.peer_connections)})")
    
    def add_viewer(self) -> bool:
        """Increment viewer count and start stream if first viewer"""
        with self.lock:
            self.viewer_count += 1
            logger.info(f"Camera {self.camera_id}: Viewer joined (count: {self.viewer_count})")
            
            # Start stream only if this is the first viewer
            if self.viewer_count == 1 and not self.is_running:
                logger.info(f"Camera {self.camera_id}: First viewer, starting stream")
                return self._start_stream()
            
            return True
    
    def remove_viewer(self) -> bool:
        """Decrement viewer count and stop stream if last viewer left"""
        with self.lock:
            if self.viewer_count > 0:
                self.viewer_count -= 1
                logger.info(f"Camera {self.camera_id}: Viewer left (count: {self.viewer_count})")
                
                # Stop stream if no viewers remain
                if self.viewer_count == 0 and self.is_running:
                    logger.info(f"Camera {self.camera_id}: No viewers, stopping stream")
                    return self._stop_stream()
            
            return True
    
    def get_status(self) -> CameraRuntimeStatus:
        """Get current runtime status"""
        with self.lock:
            uptime_seconds = None
            if self.start_time is not None:
                uptime_seconds = int(time.time() - self.start_time)
            
            return CameraRuntimeStatus(
                camera_id=self.camera_id,
                is_running=self.is_running,
                viewer_count=self.viewer_count,
                stream_type="webrtc",
                uptime_seconds=uptime_seconds,
                peer_connection_count=len(self.peer_connections)
            )
    
    def cleanup(self) -> None:
        """Cleanup resources when removing camera"""
        logger.info(f"Camera {self.camera_id}: Cleaning up")
        
        # Close all peer connections
        for pc in self.peer_connections:
            try:
                pc.close()
            except Exception as e:
                logger.error(f"Camera {self.camera_id}: Error closing peer connection: {e}")
        
        self.peer_connections.clear()
        
        # Stop stream
        self._stop_stream()


class CameraController:
    """Singleton controller for managing all camera streams"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.streams: dict[int, CameraStream] = {}
            self.streams_lock = threading.Lock()
            self.initialized = True
            logger.info("CameraController initialized")
    
    def get_camera(self, camera_config: CameraStreamConfig) -> CameraStream:
        """Get or create a camera stream"""
        with self.streams_lock:
            camera_id = camera_config.camera_id
            
            if camera_id not in self.streams:
                logger.info(f"Creating new CameraStream for camera {camera_id}")
                self.streams[camera_id] = CameraStream(camera_config)
            
            return self.streams[camera_id]
    
    def remove_camera(self, camera_id: int) -> bool:
        """Remove and cleanup a camera stream"""
        with self.streams_lock:
            if camera_id in self.streams:
                logger.info(f"Removing camera {camera_id}")
                stream = self.streams[camera_id]
                stream.cleanup()
                del self.streams[camera_id]
                return True
            return False
    

# Singleton instance 
camera_controller = CameraController()