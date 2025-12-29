from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from aiortc import RTCPeerConnection, RTCSessionDescription
import logging

## Project imports
from database.db import get_db
import crud.camera as camera_crud
from modules.camera.controller import camera_controller
from schemas.camera import CameraCreateRequest, CameraResponse, WebRTCOffer, WebRTCAnswer, CameraWithStatus, CameraRuntimeStatus
from utilities.auth import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])
logger = logging.getLogger(__name__)

@router.post("/{camera_id}/webrtc/offer", response_model=WebRTCAnswer)
async def webrtc_offer(camera_id: int, offer: WebRTCOffer, db: AsyncSession = Depends(get_db)) -> WebRTCAnswer:
    """Handle WebRTC offer from client and return answer"""
    camera_config = await camera_crud.get_camera(db, camera_id)
    if not camera_config:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    stream = camera_controller.get_camera(camera_config)
    
    # 1. Add viewer FIRST (starts stream if needed)
    stream.add_viewer()
    
    # 2. Wait for video_track to be ready (up to 10 seconds)
    import asyncio
    max_wait = 10
    wait_interval = 0.5
    waited = 0
    
    while not stream.video_track and waited < max_wait:
        await asyncio.sleep(wait_interval)
        waited += wait_interval
    
    if not stream.video_track:
        stream.remove_viewer()  # Clean up
        raise HTTPException(status_code=503, detail="Camera stream failed to start")
    
    # 3. Create peer connection
    pc = RTCPeerConnection()
    
    # 4. Add video track
    pc.addTrack(stream.video_track)
    
    # 5. Store peer connection
    stream.add_peer_connection(pc)
    
    # 6. Handle cleanup when connection closes
    @pc.on("connectionstatechange")
    async def on_state_change():
        if pc.connectionState in ["failed", "closed"]:
            logger.info(f"Camera {camera_id}: Peer connection {pc.connectionState}")
            stream.remove_peer_connection(pc)
            stream.remove_viewer()  # Decrement viewer count
    
    # 7. Complete WebRTC handshake
    await pc.setRemoteDescription(RTCSessionDescription(
        sdp=offer.sdp,
        type=offer.type
    ))
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return WebRTCAnswer(
        sdp=pc.localDescription.sdp,
        type=pc.localDescription.type
    )
     
@router.post("/create", response_model=CameraResponse, status_code=201)
async def create_camera(camera: CameraCreateRequest, db: AsyncSession = Depends(get_db)) -> CameraResponse:
    """
    Create a new camera configuration.
    
    Args:
        camera: CameraCreateRequest model with camera details
        db: Async database session
    
    Returns:
        CameraResponse: Created camera with database-generated fields
    """
    new_camera = await camera_crud.create_camera(db, camera)
    if not new_camera:
        raise HTTPException(status_code=500, detail="Failed to create camera")
    
    return new_camera

@router.get("/statuses", response_model=list[CameraWithStatus])
async def get_camera_statuses(db: AsyncSession = Depends(get_db)) -> list[CameraWithStatus]:
    """
    Get all cameras with their runtime status.
    
    Combines static camera configuration from database with runtime status
    from in-memory camera controller.
    
    Args:
        db: Async database session
    
    Returns:
        List[CameraWithStatus]: Camera configs with runtime status
    """
    # Get all cameras from database
    cameras = await camera_crud.get_cameras(db)
    
    results = []
    for camera in cameras:
        # Check if camera has an active stream in the controller
        if camera.camera_id in camera_controller.streams:
            stream = camera_controller.streams[camera.camera_id]
            status = stream.get_status()
        else:
            # Camera exists in DB but no active stream
            status = CameraRuntimeStatus(
                camera_id=camera.camera_id,
                is_running=False,
                viewer_count=0,
                stream_type="webrtc",
                uptime_seconds=None,
                peer_connection_count=0
            )
        
        # Combine camera config with status
        camera_dict = {**camera.__dict__, 'status': status}
        camera_with_status = CameraWithStatus.model_validate(camera_dict)
        results.append(camera_with_status)
    
    return results

@router.get("/{camera_id}/status", response_model=CameraRuntimeStatus)
async def get_camera_status(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
) -> CameraRuntimeStatus:
    """Get runtime status for a specific camera"""
    # Check camera exists
    camera = await camera_crud.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Get status from controller
    if camera_id in camera_controller.streams:
        stream = camera_controller.streams[camera_id]
        return stream.get_status()
    else:
        return CameraRuntimeStatus(
            camera_id=camera_id,
            is_running=False,
            viewer_count=0,
            stream_type="webrtc",
            uptime_seconds=None,
            peer_connection_count=0
        )