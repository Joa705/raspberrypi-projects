# Backend README

## FastAPI Backend for Raspberry Pi Hardware Control

This is a single-process FastAPI backend that runs on a Raspberry Pi and controls hardware modules (camera, heat sensor, light).

### Architecture

```
backend/
├── main.py              # FastAPI application entrypoint
├── api/                 # HTTP route definitions (no hardware logic)
│   ├── camera.py        # Camera endpoints
│   ├── heat.py          # Heat sensor endpoints
│   └── light.py         # Light control endpoints
│
├── modules/             # Hardware control logic (no HTTP knowledge)
│   ├── camera/
│   │   ├── controller.py  # High-level camera control
│   │   └── driver.py      # Low-level camera driver
│   ├── heat/
│   │   └── sensor.py      # Temperature/humidity sensor
│   └── light/
│       └── relay.py       # Light relay control
```

### Setup

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the server**:
   ```bash
   python main.py
   ```
   
   Or with uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### API Endpoints

#### Camera
- `GET /camera/snapshot` - Capture a single image
- `POST /camera/stream/start` - Start video streaming
- `POST /camera/stream/stop` - Stop video streaming
- `GET /camera/status` - Get camera status

#### Heat Sensor
- `GET /heat` - Get temperature and humidity
- `GET /heat/temperature` - Get temperature only
- `GET /heat/humidity` - Get humidity only

#### Light Control
- `POST /light/on` - Turn light on
- `POST /light/off` - Turn light off
- `POST /light/toggle` - Toggle light state
- `GET /light/status` - Get light status

### Mock Implementations

All hardware modules use mock implementations by default. This allows:
- Safe development on non-Raspberry Pi systems
- Testing without physical hardware
- Easy replacement with real hardware code later

To connect real hardware, replace the mock implementations in the `modules/` directory with actual GPIO/sensor code.

### Design Principles

1. **Separation of Concerns**
   - `api/` layer: HTTP routing, validation, responses
   - `modules/` layer: Hardware control only

2. **Single Process**
   - Not a microservices architecture
   - All code runs in one FastAPI process
   - Direct Python imports between layers

3. **Hardware Safety**
   - Mock implementations prevent GPIO errors
   - Safe to run on any system
   - Real hardware code can be dropped in when ready

### Development

- The server runs with auto-reload enabled in development mode
- Check the interactive API docs at `/docs` for testing endpoints
- All routes return JSON suitable for a Svelte frontend
