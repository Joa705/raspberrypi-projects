from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from aiortc import RTCPeerConnection, RTCSessionDescription

## Project imports
from database.db import get_db
import crud.camera as camera_crud
from modules.camera.controller import camera_controller
from schemas.camera import CameraCreateRequest, CameraResponse, WebRTCOffer, WebRTCAnswer

router = APIRouter()

@router.post("/{camera_id}/webrtc/offer", response_model=WebRTCAnswer)
async def webrtc_offer(camera_id: int, offer: WebRTCOffer, db: AsyncSession = Depends(get_db)) -> WebRTCAnswer:
    """Handle WebRTC offer from client and return answer"""
    import asyncio
    
    # 1. Get camera config from database
    camera_config = await camera_crud.get_camera(db, camera_id)
    if not camera_config:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # 2. Get or create camera stream
    stream = camera_controller.get_camera(camera_config)
    
    # 3. Start stream and track viewer (this creates video_track)
    stream.add_viewer()
    
    # 4. Wait for video track to be ready
    max_wait = 10  # seconds
    wait_interval = 0.5  # seconds
    waited = 0
    
    while not stream.video_track and waited < max_wait:
        await asyncio.sleep(wait_interval)
        waited += wait_interval
    
    if not stream.video_track:
        stream.remove_viewer()  # Clean up if failed
        raise HTTPException(status_code=503, detail="Camera stream failed to start")
    
    # 5. Create NEW peer connection for THIS client
    pc = RTCPeerConnection()
    
    # 6. Add camera's video track to this connection
    pc.addTrack(stream.video_track)
    
    # 7. Store the peer connection
    stream.add_peer_connection(pc)
    
    # 8. Handle cleanup when connection closes
    @pc.on("connectionstatechange")
    async def on_state_change():
        if pc.connectionState in ["failed", "closed"]:
            stream.remove_peer_connection(pc)
            stream.remove_viewer()
    
    # 9. Complete WebRTC handshake
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