# WebRTC + FFmpeg Migration TODO

## Overview
Migrate from OpenCV + WebSocket to FFmpeg + WebRTC for better performance and lower latency on Raspberry Pi.

---

## 1. Database Models (No Changes Needed)
**File:** `database/models.py`

✅ **Current `Camera` table is correct** - stores static configuration only:
- `camera_id` (Primary Key)
- `name`, `ip_address`, `username`, `password`
- `stream_quality` (stream1=HD, stream2=SD)
- `description`
- `created_at`, `updated_at`

**No changes needed** - keep database for static config only, NOT runtime state.

---

## 2. Pydantic Models (Add Runtime State Models)
**File:** `models/camera.py`

### ✅ Existing (Keep as is):
- `CameraBase` - base fields
- `CameraCreateRequest` - create new camera
- `CameraUpdate` - update camera config
- `CameraCreateResponse` - database camera response

### ⬜ TODO: Add Runtime State Models

```python
class CameraRuntimeStatus(BaseModel):
    """Runtime state from CameraStream (in-memory only)"""
    camera_id: int
    is_running: bool
    viewer_count: int
    stream_type: str = "webrtc"  # "webrtc" or "hls" 
    uptime_seconds: Optional[int] = None
    last_frame_time: Optional[datetime] = None
    peer_connection_count: int = 0  # Active WebRTC connections

class CameraWithStatus(CameraCreateResponse):
    """Combined: static config + runtime status"""
    status: CameraRuntimeStatus
```

---

## 3. Camera Controller (WebRTC Implementation)
**File:** `modules/camera/controller2.py`

### ⬜ TODO: Implement WebRTC CameraStream

**Key differences from controller.py:**

#### Replace OpenCV with FFmpeg:
- ❌ Remove: `cv2.VideoCapture`, JPEG encoding
- ✅ Add: FFmpeg subprocess with H.264 copy codec
- ✅ Benefit: No re-encoding = 90% less CPU usage

#### Add WebRTC Support:
```python
class CameraStream:
    def __init__(self, camera_id: int, camera_data: CameraBase):
        self.camera_id = camera_id
        # Static config
        self.name = camera_data.name
        self.ip_address = camera_data.ip_address
        self.username = camera_data.username
        self.password = camera_data.password
        self.stream_quality = camera_data.stream_quality
        
        # Runtime state (in-memory)
        self.is_running = False
        self.viewer_count = 0
        self.peer_connections = []  # List of RTCPeerConnection
        self.ffmpeg_process = None
        self.video_track = None  # MediaStreamTrack
        self.start_time = None
        self.lock = threading.Lock()
```

#### Key Methods to Implement:
- ⬜ `_start_ffmpeg()` - Start FFmpeg with H.264 output
- ⬜ `_stop_ffmpeg()` - Terminate FFmpeg process
- ⬜ `add_peer_connection(pc: RTCPeerConnection)` - Add WebRTC peer
- ⬜ `remove_peer_connection(pc: RTCPeerConnection)` - Remove peer
- ⬜ `add_viewer()` - Increment count, start stream if first viewer
- ⬜ `remove_viewer()` - Decrement count, stop stream if last viewer
- ⬜ `get_status()` - Return CameraRuntimeStatus model

#### FFmpeg Command Example:
```bash
ffmpeg \
  -rtsp_transport tcp \
  -i rtsp://username:password@192.168.1.100:554/stream2 \
  -c:v copy \              # Copy H.264 (no re-encoding!)
  -f rtsp \                # Output format
  rtsp://localhost:8554/camera1
```

Or output to RTP for WebRTC consumption.

### ⬜ TODO: Update CameraController

Keep the singleton pattern and camera management logic:
- ✅ `get_camera(camera_id)` - Get or create CameraStream
- ✅ `remove_camera(camera_id)` - Stop and remove stream
- ⬜ `get_camera_status(camera_id)` - Return CameraRuntimeStatus
- ⬜ `list_all_statuses()` - Return all camera runtime states

---

## 4. API Endpoints (WebRTC Signaling)
**File:** `api/camera2.py`

### ⬜ TODO: Implement WebRTC Endpoints

#### A. Configuration Endpoints (existing pattern):
- ✅ `GET /cameras` - List all cameras (from DB)
- ✅ `GET /cameras/{camera_id}` - Get camera config (from DB)
- ✅ `POST /cameras/create` - Create camera (DB insert)
- ✅ `PUT /cameras/{camera_id}` - Update camera config (DB update)
- ✅ `DELETE /cameras/{camera_id}` - Delete camera (DB + stop stream)

#### B. Runtime Status Endpoints (NEW):
- ⬜ `GET /cameras/{camera_id}/status` - Get CameraRuntimeStatus
- ⬜ `GET /cameras/status/all` - Get all cameras with status
- ⬜ `GET /cameras/{camera_id}/combined` - Config + Status

#### C. WebRTC Signaling Endpoints (NEW):
```python
@router.post("/{camera_id}/webrtc/offer")
async def webrtc_offer(camera_id: int, offer: dict):
    """
    WebRTC signaling endpoint
    
    Request body:
    {
        "sdp": "v=0\r\no=- ...",
        "type": "offer"
    }
    
    Response:
    {
        "sdp": "v=0\r\no=- ...",
        "type": "answer"
    }
    """
    # 1. Get camera from DB
    # 2. Get or create CameraStream
    # 3. Create RTCPeerConnection
    # 4. Add camera video track
    # 5. Process offer, create answer
    # 6. Add viewer to CameraStream
    # 7. Return answer SDP
```

#### D. Optional - Keep WebSocket for backward compatibility:
- ⬜ `WS /cameras/{camera_id}/ws` - Old WebSocket endpoint (optional)

---

## 5. Dependencies to Install

### ⬜ TODO: Add to `requirements.txt`:
```txt
aiortc>=1.6.0          # WebRTC for Python
av>=11.0.0             # PyAV for media handling
aiohttp>=3.9.0         # Async HTTP (if not already)
```

### ⬜ TODO: System dependencies (on Raspberry Pi):
```bash
sudo apt-get update
sudo apt-get install -y \
  ffmpeg \
  libavcodec-dev \
  libavformat-dev \
  libavdevice-dev \
  libavutil-dev \
  libswscale-dev \
  libswresample-dev \
  libavfilter-dev \
  pkg-config
```

---

## 6. Frontend Changes
**File:** `frontend/src/lib/Cameras.svelte` (or similar)

### ⬜ TODO: Replace WebSocket with WebRTC Client

#### Old (WebSocket):
```javascript
const ws = new WebSocket(`ws://server/cameras/${cameraId}/ws`);
ws.onmessage = (event) => {
  videoElement.src = URL.createObjectURL(new Blob([event.data]));
};
```

#### New (WebRTC):
```javascript
const pc = new RTCPeerConnection();

pc.ontrack = (event) => {
  videoElement.srcObject = event.streams[0];
};

async function startStream(cameraId) {
  pc.addTransceiver('video', { direction: 'recvonly' });
  
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  
  const response = await fetch(`/api/cameras/${cameraId}/webrtc/offer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sdp: pc.localDescription.sdp,
      type: pc.localDescription.type
    })
  });
  
  const answer = await response.json();
  await pc.setRemoteDescription(answer);
}

// Cleanup when leaving page
window.addEventListener('beforeunload', () => {
  pc.close();
});
```

---

## 7. Testing Checklist

### ⬜ Unit Tests:
- CameraStream lifecycle (start/stop based on viewers)
- Viewer counting (add/remove)
- FFmpeg process management

### ⬜ Integration Tests:
- Create camera → Start stream → Stop stream
- Multiple viewers on same camera
- WebRTC offer/answer exchange

### ⬜ Manual Tests:
- [ ] Single client connects → Stream starts
- [ ] Second client joins → Same stream instance used
- [ ] All clients disconnect → Stream stops (30s grace period)
- [ ] Reconnect before timeout → Stream continues
- [ ] Check CPU usage (should be ~70% lower than OpenCV)
- [ ] Check latency (should be <1 second)

---

## 8. Performance Comparison

### Expected Results:

| Metric | OpenCV + WebSocket | FFmpeg + WebRTC |
|--------|-------------------|-----------------|
| **CPU Usage** | ~40-60% (encoding JPEG) | ~5-10% (copy codec) |
| **Latency** | 2-5 seconds | <500ms |
| **Quality** | JPEG artifacts | Native H.264 |
| **Bandwidth** | High (JPEG) | Lower (H.264) |

---

## 9. Migration Path

### Phase 1: Backend (Current Focus)
1. ✅ Design database/runtime separation
2. ⬜ Add Pydantic runtime models
3. ⬜ Implement controller2.py with FFmpeg + WebRTC
4. ⬜ Implement camera2.py API endpoints
5. ⬜ Test with curl/Postman

### Phase 2: Frontend
1. ⬜ Add WebRTC client code
2. ⬜ Test single camera stream
3. ⬜ Test multiple viewers
4. ⬜ Add error handling

### Phase 3: Deployment
1. ⬜ Install dependencies on Pi
2. ⬜ Deploy and test on real hardware
3. ⬜ Monitor performance
4. ⬜ Remove old controller.py and camera.py (when stable)

---

## 10. Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      Database (PostgreSQL)               │
│  Camera Table: id, name, ip, username, password, etc.   │
└─────────────────────────────────────────────────────────┘
                          ↓ Read config
┌─────────────────────────────────────────────────────────┐
│              CameraController (Singleton)                │
│  ┌─────────────────────────────────────────────────┐   │
│  │  CameraStream (camera_id=1)                     │   │
│  │  - is_running: True                             │   │
│  │  - viewer_count: 3                              │   │
│  │  - ffmpeg_process: <Process>                    │   │
│  │  - peer_connections: [pc1, pc2, pc3]           │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  CameraStream (camera_id=2)                     │   │
│  │  - is_running: False                            │   │
│  │  - viewer_count: 0                              │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
           ↓ Video Track                    ↓ Status API
┌──────────────────────┐         ┌─────────────────────────┐
│  WebRTC Endpoints    │         │   Status Endpoints      │
│  /webrtc/offer       │         │   /status               │
└──────────────────────┘         └─────────────────────────┘
           ↓                                  ↓
┌──────────────────────┐         ┌─────────────────────────┐
│  Browser Client 1    │         │   Admin Dashboard       │
│  (WebRTC video)      │         │   (View all cameras)    │
└──────────────────────┘         └─────────────────────────┘
```

---

## Questions to Consider

- [ ] Do we need STUN/TURN servers for NAT traversal? (Probably not if Pi and clients on same network)
- [ ] Should we support HLS as fallback for older browsers?
- [ ] How to handle multiple streams from same camera (different quality levels)?
- [ ] Authentication/authorization for camera access?

---

## Resources

- aiortc docs: https://aiortc.readthedocs.io/
- FFmpeg RTSP streaming: https://trac.ffmpeg.org/wiki/StreamingGuide
- WebRTC API: https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API
