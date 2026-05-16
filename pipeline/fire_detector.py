"""pipeline/fire_detector.py
Fire and smoke detection module."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Optional

from core.config import FIRE_CONFIDENCE, SMOKE_CONFIDENCE, CONFIRM_FRAMES, ALERT_COOLDOWN
from core import config as cfg
FIRE_CONFIDENCE = getattr(cfg, 'FIRE_CONFIDENCE', 0.6)
SMOKE_CONFIDENCE = getattr(cfg, 'SMOKE_CONFIDENCE', 0.5)
CONFIRM_FRAMES = getattr(cfg, 'CONFIRM_FRAMES', 5)
ALERT_COOLDOWN = getattr(cfg, 'ALERT_COOLDOWN', 30)
from pipeline.detector import Detection


class FireActivityType(StrEnum):
    FIRE = "fire"
    SMOKE = "smoke"


class EventSeverity(Enum):
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class FireEvent:
    activity_type: FireActivityType
    track_ids: list[int]
    camera_id: str
    severity: EventSeverity = EventSeverity.CRITICAL
    event_id: str = field(default_factory=lambda: f"fire_{int(time.time()*1000)}")
    timestamp: float = field(default_factory=time.time)
    extra: dict = field(default_factory=dict)


class FireDetector:
    """Detects fire and smoke using YOLO model."""

    def __init__(
        self,
        model_path: str = "fire_smoke_best.pt",
        fire_conf: float = FIRE_CONFIDENCE,
        smoke_conf: float = SMOKE_CONFIDENCE,
        confirm_frames: int = CONFIRM_FRAMES,
    ):
        self.model_path = model_path
        self.fire_conf = fire_conf
        self.smoke_conf = smoke_conf
        self.confirm_frames = confirm_frames
        self._fire_count = 0
        self.smoke_count = 0
        self.last_alert_time = 0.0
        self._alert_cooldown = ALERT_COOLDOWN
        self._model = None

    def _load_model(self) -> bool:
        """Lazily load the YOLO model."""
        if self._model is None:
            try:
                from ultralytics import YOLO
                print(f"[FireDetector] loading {self.model_path}...")
                self._model = YOLO(self.model_path)
                print("[FireDetector] ready")
            except Exception as e:
                print(f"[FireDetector] failed to load model: {e}")
                return False
        return True

    def detect(self, frame) -> list[Detection]:
        """Run fire/smoke detection on a frame."""
        if not self._load_model():
            return []
        
        try:
            results = self._model.predict(frame, verbose=False)[0]
            detections = []
            for box in results.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                label = self._model.names[cls_id]
                detections.append(Detection(
                    bbox=(x1, y1, x2, y2),
                    confidence=conf,
                    class_id=cls_id,
                    class_name=label,
                    track_id=None,
                ))
            return detections
        except:
            return []

    def analyze(self, detections: list[Detection], camera_id: str = "cam-0") -> list[FireEvent]:
        """Analyze detections and return fire/smoke events."""
        events = []
        now = time.time()
        fire_detected = False
        smoke_detected = False

        for d in detections:
            if d.class_name == "fire" and d.confidence >= self.fire_conf:
                fire_detected = True
            elif d.class_name == "smoke" and d.confidence >= self.smoke_conf:
                smoke_detected = True

        if fire_detected:
            self._fire_count += 1
        else:
            self._fire_count = 0

        if smoke_detected:
            self.smoke_count += 1
        else:
            self.smoke_count = 0

        fire_confirmed = self._fire_count >= self.confirm_frames
        smoke_confirmed = self.smoke_count >= self.confirm_frames

        if fire_confirmed and now - self.last_alert_time >= self._alert_cooldown:
            self.last_alert_time = now
            events.append(FireEvent(
                activity_type=FireActivityType.FIRE,
                track_ids=[],
                camera_id=camera_id,
                severity=EventSeverity.CRITICAL,
                extra={"confidence": self._fire_count / self.confirm_frames, "count": len([d for d in detections if d.class_name == "fire"])},
            ))
        elif smoke_confirmed and now - self.last_alert_time >= self._alert_cooldown:
            self.last_alert_time = now
            events.append(FireEvent(
                activity_type=FireActivityType.SMOKE,
                track_ids=[],
                camera_id=camera_id,
                severity=EventSeverity.WARNING,
                extra={"confidence": self.smoke_count / self.confirm_frames, "count": len([d for d in detections if d.class_name == "smoke"])},
            ))

        return events
