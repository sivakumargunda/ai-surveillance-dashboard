"""
api.py
FastAPI application for the surveillance system.
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from typing import List, Optional

import cv2
from fastapi import Depends, FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
except ImportError:
    genai = None
    load_dotenv = None

from core.camera_manager import camera_manager
from core.models import Alert, Zone, create_tables, get_db
from core.config import AUTO_START_CAMERAS, CAM_MAX_RETRIES, CAMERA_REGISTRY_PATH, STREAM_FPS_LIMIT



app = FastAPI(title="Surveillance API", version="1.0.0")

if load_dotenv:
    load_dotenv()

gemini_model = None
if genai and os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# CORS middleware for React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API responses
class AlertResponse(BaseModel):
    id: int
    state: str
    activity_type: str
    track_ids: List[int]
    camera_id: str
    timestamp: datetime
    message: Optional[str]
    extra_data: Optional[dict]
    snapshot_path: Optional[str]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @classmethod
    def from_orm(cls, obj):
        """Convert database object to response model, handling JSON deserialization."""
        data = {
            'id': obj.id,
            'state': obj.event_state.lower(),
            'activity_type': obj.activity_type,
            'track_ids': json.loads(obj.track_ids) if obj.track_ids else [],
            'camera_id': obj.camera_id,
            'timestamp': obj.timestamp,
            'message': obj.message,
            'extra_data': json.loads(obj.extra_data) if obj.extra_data else None,
            'snapshot_path': obj.snapshot_path
        }
        return cls(**data)

class AlertCreate(BaseModel):
    activity_type: str
    track_ids: List[int]
    camera_id: str
    message: Optional[str] = None
    extra_data: Optional[dict] = None
    snapshot_path: Optional[str] = None


SYSTEM_CONTEXT = """
You are an enterprise AI Surveillance Intelligence Assistant for Sentinel AI.
You analyze surveillance data, alerts, camera feeds, and security incidents.
Always respond professionally, concisely, and in bullet points where helpful.
Format responses clearly for a security operations dashboard.
Current time: {time}
"""

MOCK_DATA = """
Today's data:
- Total cameras: 16 (12 active, 4 offline)
- Critical alerts: 12 (most from Warehouse Zone B)
- Peak activity: 8 PM to 10 PM
- Intrusion alerts: 3 (between 7 PM - 9 PM)
- Occupancy events: 14
- Most active camera: Camera 07 - Warehouse Zone B
- Suspicious movement detected near: Restricted Zone C
- Retail Zone traffic: 340 people (up 18% from yesterday)
- Threat level: Medium
"""


class ChatRequest(BaseModel):
    message: str


class IncidentRequest(BaseModel):
    zone: str
    start_time: str
    end_time: str


def generate_gemini_response(prompt: str) -> str:
    if gemini_model is None:
        raise HTTPException(
            status_code=503,
            detail="Gemini AI is not configured. Set GEMINI_API_KEY and install google-generativeai.",
        )
    response = gemini_model.generate_content(prompt)
    return response.text


class ZoneResponse(BaseModel):
    id: int
    camera_id: str
    zone_name: str
    zone_type: str
    points: list[list[float]]
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            camera_id=obj.camera_id,
            zone_name=obj.zone_name,
            zone_type=obj.zone_type,
            points=json.loads(obj.points) if obj.points else [],
            created_at=obj.created_at,
        )


class ZoneCreate(BaseModel):
    camera_id: str
    zone_name: str
    zone_type: str = "intrusion"
    points: list[list[float]]


class LiveStats(BaseModel):
    people: int = 0
    vehicles: int = 0
    fps: float = 0.0
    tracked: int = 0
    timestamp: Optional[str] = None


latest_live_stats = LiveStats(timestamp=datetime.utcnow().isoformat())

@app.on_event("startup")
def startup_event():
    """Create database tables and start the camera manager."""
    create_tables()
    if AUTO_START_CAMERAS:
        camera_manager.start()


@app.get("/health")
def health():
    """Lightweight deployment health check."""
    return {
        "status": "ok",
        "model": "gemini-1.5-flash" if gemini_model else "not_configured",
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    prompt = f"""
{SYSTEM_CONTEXT.format(time=datetime.now().strftime('%Y-%m-%d %H:%M'))}

Surveillance context:
{MOCK_DATA}

User question: {req.message}

Respond professionally. Use bullet points. Keep it under 120 words.
"""
    return {"response": generate_gemini_response(prompt)}


@app.post("/incident-summary")
async def incident_summary(req: IncidentRequest):
    prompt = f"""
{SYSTEM_CONTEXT.format(time=datetime.now().strftime('%Y-%m-%d %H:%M'))}

Generate a professional incident summary report for:
Zone: {req.zone}
Time period: {req.start_time} to {req.end_time}

{MOCK_DATA}

Format as a structured incident report with:
- Overview
- Key events (bullet points)
- Risk assessment
- Recommended actions
Keep under 150 words.
"""
    return {"summary": generate_gemini_response(prompt)}


@app.post("/analytics-query")
async def analytics_query(req: ChatRequest):
    prompt = f"""
{SYSTEM_CONTEXT.format(time=datetime.now().strftime('%Y-%m-%d %H:%M'))}

{MOCK_DATA}

Analytics question: {req.message}

Respond with specific data points, numbers, and trends.
Use bullet points. Under 100 words.
"""
    return {"response": generate_gemini_response(prompt)}

@app.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    skip: int = 0,
    limit: int = 100,
    camera_id: Optional[str] = None,
    activity_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get alerts with optional filtering."""
    query = db.query(Alert)

    if camera_id:
        query = query.filter(Alert.camera_id == camera_id)

    if activity_type:
        query = query.filter(Alert.activity_type == activity_type)

    alerts = query.order_by(Alert.timestamp.desc()).offset(skip).limit(limit).all()
    return [AlertResponse.from_orm(alert) for alert in alerts]

@app.get("/alerts/stats", response_model=dict)
def get_alert_stats(db: Session = Depends(get_db)):
    """Get alert statistics."""
    from sqlalchemy import func

    # Count by activity type
    type_stats = db.query(
        Alert.activity_type,
        func.count(Alert.id).label("count")
    ).group_by(Alert.activity_type).all()

    # Count by camera
    camera_stats = db.query(
        Alert.camera_id,
        func.count(Alert.id).label("count")
    ).group_by(Alert.camera_id).all()

    # Recent alerts (last 24 hours)
    from datetime import timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_count = db.query(Alert).filter(Alert.timestamp >= yesterday).count()

    return {
        "by_type": {stat.activity_type: stat.count for stat in type_stats},
        "by_camera": {stat.camera_id: stat.count for stat in camera_stats},
        "recent_24h": recent_count,
        "total": sum(stat.count for stat in type_stats)
    }


@app.get("/live-stats", response_model=LiveStats)
def get_live_stats():
    """Get the latest live people/vehicle count from the pipeline."""
    return latest_live_stats


@app.post("/live-stats", response_model=LiveStats)
def update_live_stats(stats: LiveStats):
    """Update live people/vehicle count from the pipeline."""
    global latest_live_stats
    latest_live_stats = LiveStats(
        people=stats.people,
        vehicles=stats.vehicles,
        fps=stats.fps,
        tracked=stats.tracked,
        timestamp=datetime.utcnow().isoformat(),
    )
    return latest_live_stats


@app.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get a specific alert by ID."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse.from_orm(alert)


@app.post("/alert", response_model=AlertResponse)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    """Create a new alert."""
    db_alert = Alert(
        activity_type=alert.activity_type,
        event_state="START",  # Default for created alerts
        track_ids=json.dumps(alert.track_ids),
        camera_id=alert.camera_id,
        message=alert.message,
        extra_data=json.dumps(alert.extra_data) if alert.extra_data else None,
        snapshot_path=alert.snapshot_path
    )

    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def _validate_zone_points(points: list[list[float]]) -> list[list[float]]:
    if len(points) < 3:
        raise HTTPException(status_code=400, detail="Zone must have at least 3 points")

    cleaned = []
    for point in points:
        if len(point) != 2:
            raise HTTPException(status_code=400, detail="Each zone point must be [x, y]")
        try:
            x = float(point[0])
            y = float(point[1])
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Zone point coordinates must be numeric")
        if x < 0 or y < 0:
            raise HTTPException(status_code=400, detail="Zone point coordinates must be non-negative")
        cleaned.append([x, y])
    return cleaned


@app.post("/zones", response_model=ZoneResponse)
def create_zone(zone: ZoneCreate, db: Session = Depends(get_db)):
    """Create a polygon zone for a camera."""
    camera = camera_manager.registry.get(zone.camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera '{zone.camera_id}' not found")

    zone_name = zone.zone_name.strip()
    zone_type = zone.zone_type.strip().lower()
    if not zone_name:
        raise HTTPException(status_code=400, detail="Zone name is required")
    if zone_type not in {"intrusion", "queue", "fire_risk"}:
        raise HTTPException(status_code=400, detail="Unsupported zone type")

    db_zone = Zone(
        camera_id=zone.camera_id,
        zone_name=zone_name,
        zone_type=zone_type,
        points=json.dumps(_validate_zone_points(zone.points)),
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return ZoneResponse.from_orm(db_zone)


@app.get("/zones/{camera_id}", response_model=List[ZoneResponse])
def get_zones(camera_id: str, db: Session = Depends(get_db)):
    """Get all zones configured for a camera."""
    zones = db.query(Zone).filter(Zone.camera_id == camera_id).order_by(Zone.id.asc()).all()
    return [ZoneResponse.from_orm(zone) for zone in zones]


@app.delete("/zones/{zone_id}")
def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    """Delete a configured zone."""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(zone)
    db.commit()
    return {"message": f"Zone {zone_id} deleted successfully"}


@app.delete("/zones/camera/{camera_id}")
def delete_camera_zones(camera_id: str, db: Session = Depends(get_db)):
    """Delete all zones for a camera."""
    deleted = db.query(Zone).filter(Zone.camera_id == camera_id).delete()
    db.commit()
    return {"message": f"Deleted {deleted} zones for {camera_id}", "deleted": deleted}

@app.get("/clips/{filename}")
def get_clip(filename: str):
    """Serve video clips.""" 
    from pathlib import Path
    clip_path = Path("artifacts/clips") / filename
    if not clip_path.exists():
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(clip_path)

@app.get("/snapshots/{filename}")
def get_snapshot(filename: str):
    """Serve snapshot images."""
    from pathlib import Path
    snapshot_path = Path("artifacts/alerts") / filename
    if not snapshot_path.exists():
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return FileResponse(snapshot_path)


# ─────────────────────────────────────────────────────────────────────────────
# Live Stream Endpoints (MJPEG)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/stream/{camera_id}")
async def get_stream(camera_id: str):
    """MJPEG stream from the latest annotated or raw camera buffer."""
    async def generate():
        while True:
            frame = camera_manager.get_stream_frame(camera_id)
            if frame is not None:
                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 55])
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
            await asyncio.sleep(1.0 / STREAM_FPS_LIMIT)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace;boundary=frame"
    )


@app.get("/cameras/{camera_id}/status")
def get_camera_status(camera_id: str):
    return camera_manager.get_status(camera_id)


class CameraCreate(BaseModel):
    url: HttpUrl
    name: Optional[str] = None
    rotate: Optional[int] = 0


def _normalize_camera_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.path in {"", "/"}:
        return urlunparse(parsed._replace(path="/video"))
    return url


@app.get("/cameras")
def list_cameras():
    cameras = camera_manager.registry.get_all()
    statuses = camera_manager.get_all_statuses()
    return [
        {
            **cam,
            "status": statuses.get(cam["id"], {}).get("status", "offline"),
            "fps": statuses.get(cam["id"], {}).get("fps", 0),
            "people": statuses.get(cam["id"], {}).get("people", 0),
            "events": statuses.get(cam["id"], {}).get("events", []),
        }
        for cam in cameras
    ]


@app.post("/cameras")
def add_camera(camera: CameraCreate):
    camera_url = _normalize_camera_url(str(camera.url))
    cam = camera_manager.registry.add(camera_url, camera.name or f"Camera {len(camera_manager.registry.load()) + 1}")
    camera_manager.add_camera(cam["id"], cam["url"], rotate=camera.rotate or cam.get("rotate", 0))
    return cam


@app.delete("/cameras/{camera_id}")
def delete_camera(camera_id: str, db: Session = Depends(get_db)):
    # Remove from camera manager (stops worker and engine)
    camera_manager.remove_camera(camera_id)
    # Remove from registry
    removed = camera_manager.registry.remove(camera_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found in registry")
    db.query(Zone).filter(Zone.camera_id == camera_id).delete()
    db.commit()
    return {"message": f"Camera {camera_id} deleted successfully"}


@app.get("/system/stats")
def get_system_stats():
    return camera_manager.get_all_statuses()


@app.get("/live-stats", response_model=LiveStats)
def get_live_stats():
    statuses = camera_manager.get_all_statuses()
    total_people = sum(int(s.get("people", 0)) for s in statuses.values())
    total_fps = sum(float(s.get("fps", 0)) for s in statuses.values())
    camera_count = len(statuses)
    return LiveStats(
        people=total_people,
        vehicles=0,
        fps=round(total_fps / camera_count, 1) if camera_count else 0.0,
        tracked=total_people,
        timestamp=datetime.utcnow().isoformat(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Detections JSON Endpoint
# ─────────────────────────────────────────────────────────────────────────────

class DetectionResponse(BaseModel):
    track_id: Optional[int]
    type: str
    confidence: float
    bbox: list


class StatsResponse(BaseModel):
    people: int
    vehicles: int
    tracked: int
    fps: float


@app.post("/register-frame")
async def register_frame(data: dict):
    """Receive frame from pipeline for MJPEG streaming."""
    import base64
    import numpy as np

    camera_id = data.get("camera_id", "cam-0")
    frame_b64 = data.get("frame_b64", "")

    if frame_b64:
        try:
            img_bytes = base64.b64decode(frame_b64)
            np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is not None:
                worker = camera_manager.workers.get(camera_id)
                if worker:
                    worker.set_stream_frame(frame)
                return {"status": "ok"}
        except Exception:
            pass
    return {"status": "error"}


@app.get("/detections/{camera_id}", response_model=dict)
def get_detections(camera_id: str):
    """Get current detections for a camera as structured JSON."""
    status = camera_manager.get_status(camera_id)
    return {
        "camera_id": camera_id,
        "timestamp": datetime.utcnow().isoformat(),
        "detections": [],
        "has_stream": camera_manager.get_stream_frame(camera_id) is not None,
        "stats": {
            "people": status.get("people", 0),
            "vehicles": 0,
            "tracked": status.get("people", 0),
            "fps": status.get("fps", 0),
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    q = camera_manager.get_event_queue()
    if q is None:
        await websocket.close(code=1011)
        return

    while True:
        try:
            event = q.get_nowait()
            await websocket.send_json(event)
        except queue.Empty:
            await asyncio.sleep(0.1)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
