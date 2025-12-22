# Camera Backend - Raspberry Pi

Simple FastAPI backend for handling Raspberrypi modules and svelte frontend

## Project Structure

```
backend/
├── main.py             # FastAPI application
├── config.py           # Configuration
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
├── routes/
│   └── camera.py       # Camera endpoints
├── models/
│       └── schemas.py  # Pydantic models
└── database/
    ├── db.py           # Database connection
    └── models.py       # SQLAlchemy models
```

## API Endpoints
- `/api/modules`
- `/api/camera`

### System Endpoints
- `GET /` - API info
- `GET /health` - Health check
- `GET /api/docs` - Interactive API documentation

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` if needed:
```env
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite+aiosqlite:///./sqlite.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Run

```bash
uvicorn main:app --reload
```

Or:
```bash
python main.py
```

### 4. Test

Visit:
- **API Docs**: http://localhost:8000/api/docs
- **Health**: http://localhost:8000/health


## Database

Uses SQLite by default. Data stored in `sqlite.db`:


## Production Deployment

### Systemd Service

Create `/etc/systemd/system/backend.service`:

```ini
[Unit]
Description=Raspberrypi Backend API
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/raspberrypi-projects/backend
Environment="PATH=/home/pi/raspberrypi-projects/backend/venv/bin"
ExecStart=/home/pi/raspberrypi-projects/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable backend
sudo systemctl start backend
```

## Related

- [Main Project README](../README.md)
- [Architecture Docs](../docs/architecture.md)
