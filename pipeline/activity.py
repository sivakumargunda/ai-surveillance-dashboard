"""
pipeline/activity.py
────────────────────
Rule-based activity detection on top of tracked detections.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Dict, Optional, Set

import cv2
import numpy as np

from core.config import (
    CROWD_THRESHOLD,
    EVENT_MIN_DURATION,
    EVENT_TRACK_IOU,
    ZONE_INTRUSION_RECT,
    ZONE_INTRUSION_DEFAULT_TOP_RIGHT_HEIGHT_RATIO,
    ZONE_INTRUSION_DEFAULT_TOP_RIGHT_WIDTH_RATIO,
)
from pipeline.detector import Detection


def _parse_zone_rect(value: str) -> tuple[float, float, float, float] | None:
    if not value:
        return None
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if len(parts) != 4:
        return None
    try:
        return tuple(float(p) for p in parts)
    except ValueError:
        return None


def _clamp_ratio(value: float, fallback: float) -> float:
    if value <= 0:
        return fallback
    return min(value, 1.0)


class EventState(Enum):
    START = "start"
    ACTIVE = "active"
    UPDATE = "update"
    END = "end"

class ActivityType(StrEnum):
    CROWD = "crowd"
    ZONE_INTRUSION = "zone_intrusion"

from core.config import EVENT_MIN_DURATION, EVENT_TRACK_IOU

@dataclass
class ActivityEvent:
    activity_type: ActivityType
    track_ids: list[int]
    camera_id: str
    state: EventState
    event_id: str
    timestamp: float
    extra: dict = field(default_factory=dict)

    def __str__(self) -> str:
        ids = ", ".join(str(t) for t in self.track_ids)
        extra = "  " + "  ".join(f"{k}={v}" for k, v in self.extra.items()) if self.extra else ""
        return f"[{self.activity_type.upper()}] state={self.state.value} id={self.event_id[:8]} camera={self.camera_id} tracks=[{ids}]{extra}"


def is_inside_zone(box, zone):
    x1, y1, x2, y2 = box
    zx1, zy1, zx2, zy2 = zone

    return not (x2 < zx1 or x1 > zx2 or y2 < zy1 or y1 > zy2)


def is_center_inside_polygon(box, points: list[list[float]]) -> bool:
    x1, y1, x2, y2 = box
    center = ((x1 + x2) / 2, (y1 + y2) / 2)
    polygon = np.array(points, dtype=np.float32)
    return cv2.pointPolygonTest(polygon, center, False) >= 0

def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = ix * iy
    if inter == 0:
        return 0.0
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union else 0.0


class ActivityAnalyzer:
    """
    Stateful analyzer — call analyze() once per frame.
    """

    def __init__(
        self,
        crowd_threshold: int = CROWD_THRESHOLD,
    ) -> None:
        self.crowd_threshold = crowd_threshold
        self._configured_zone_rect = _parse_zone_rect(ZONE_INTRUSION_RECT)
        self.zone_rect = self._configured_zone_rect
        self._default_zone_width_ratio = _clamp_ratio(
            ZONE_INTRUSION_DEFAULT_TOP_RIGHT_WIDTH_RATIO,
            0.30,
        )
        self._default_zone_height_ratio = _clamp_ratio(
            ZONE_INTRUSION_DEFAULT_TOP_RIGHT_HEIGHT_RATIO,
            0.30,
        )
        self._first_seen: dict[int, float] = {}
        self._zone_intruders: set[int] = set()
        self._active_events: Dict[str, Dict[str, object]] = {}  # (camera, type): {event_id: {'start_time': float, 'tracks': set[int]}}
        self._crowd_state = 'inactive'
        self._crowd_exit_timer = 0.0
        self._crowd_cooldown_end = 0.0
        self._last_crowd_time = 0.0

    def analyze(
        self,
        detections: list[Detection],
        camera_id: str,
        frame_shape: tuple[int, ...] | None = None,
        zones: list[dict] | None = None,
    ) -> list[ActivityEvent]:
        events: list[ActivityEvent] = []
        now = time.time()
        self._ensure_zone_rect(frame_shape)

        active_ids = {d.track_id for d in detections if d.track_id is not None}
        for tid in list(self._first_seen):
            if tid not in active_ids:
                del self._first_seen[tid]

        for d in detections:
            if d.track_id is not None and d.track_id not in self._first_seen:
                self._first_seen[d.track_id] = now

        # Process zone intrusion
        zone_events = self._process_zone_intrusion(detections, camera_id, now, zones or [])
        events.extend(zone_events)

        # Process crowd
        crowd_events = self._process_crowd(detections, camera_id, now, active_ids)
        events.extend(crowd_events)

        return events

    def _ensure_zone_rect(self, frame_shape: tuple[int, ...] | None) -> None:
        if self._configured_zone_rect is not None:
            x1, y1, x2, y2 = self._configured_zone_rect
            if frame_shape:
                frame_h, frame_w = frame_shape[0], frame_shape[1]
                x1 = max(0, min(x1, frame_w))
                y1 = max(0, min(y1, frame_h))
                x2 = max(x1, min(x2, frame_w))
                y2 = max(y1, min(y2, frame_h))
            self.zone_rect = (x1, y1, x2, y2)
            return

        if frame_shape is None or len(frame_shape) < 2:
            return

        frame_h, frame_w = frame_shape[0], frame_shape[1]
        if frame_w <= 1 or frame_h <= 1:
            return

        zone_w = max(1, int(frame_w * self._default_zone_width_ratio))
        zone_h = max(1, int(frame_h * self._default_zone_height_ratio))

        x1 = max(0, frame_w - zone_w)
        y1 = 0
        x2 = frame_w - 1
        y2 = min(frame_h - 1, zone_h)

        self.zone_rect = (float(x1), float(y1), float(x2), float(y2))

    def _process_zone_intrusion(
        self,
        detections: list[Detection],
        camera_id: str,
        now: float,
        zones: list[dict],
    ) -> list[ActivityEvent]:
        intrusion_zones = [z for z in zones if z.get("zone_type") == "intrusion" and len(z.get("points", [])) >= 3]
        if not intrusion_zones and self.zone_rect is not None:
            x1, y1, x2, y2 = self.zone_rect
            intrusion_zones = [{
                "id": "default",
                "zone_name": "Restricted Zone",
                "zone_type": "intrusion",
                "rect": [x1, y1, x2, y2],
            }]

        if not intrusion_zones:
            return []

        events = []
        all_intruders: set[int] = set()

        for zone in intrusion_zones:
            zone_id = str(zone.get("id", "default"))
            zone_name = zone.get("zone_name") or zone.get("name") or "Restricted Zone"
            key = (camera_id, ActivityType.ZONE_INTRUSION, zone_id)
            if key not in self._active_events:
                self._active_events[key] = {}

            current_intruders: Dict[int, Detection] = {}
            for d in detections:
                if d.track_id is None or d.class_name != "person":
                    continue
                if zone.get("points"):
                    inside = is_center_inside_polygon(d.bbox, zone["points"])
                else:
                    inside = is_inside_zone(d.bbox, zone["rect"])
                if inside:
                    current_intruders[d.track_id] = d

            current_tracks = set(current_intruders)
            all_intruders.update(current_tracks)
            active = self._active_events[key]

            for event_id, data in list(active.items()):
                old_tracks: Set[int] = data['tracks']
                overlap = len(current_tracks & old_tracks) / len(old_tracks | current_tracks) if old_tracks or current_tracks else 0
                if overlap < EVENT_TRACK_IOU:
                    event = ActivityEvent(
                        activity_type=ActivityType.ZONE_INTRUSION,
                        track_ids=list(old_tracks),
                        camera_id=camera_id,
                        state=EventState.END,
                        event_id=event_id,
                        timestamp=now,
                        extra=data.get('extra', {})
                    )
                    events.append(event)
                    del active[event_id]

            best_match = None
            best_overlap = 0
            for event_id, data in active.items():
                old_tracks: Set[int] = data['tracks']
                overlap = len(current_tracks & old_tracks) / len(old_tracks | current_tracks) if old_tracks or current_tracks else 0
                if overlap > best_overlap:
                    best_match = event_id
                    best_overlap = overlap

            event_extra = {
                "zone_id": zone_id,
                "zone_name": zone_name,
                "zone_type": "intrusion",
                "count": len(current_tracks),
            }

            if best_match and best_overlap >= EVENT_TRACK_IOU:
                active[best_match]['tracks'] = current_tracks
                active[best_match]['extra'] = event_extra
                event = ActivityEvent(
                    activity_type=ActivityType.ZONE_INTRUSION,
                    track_ids=list(current_tracks),
                    camera_id=camera_id,
                    state=EventState.UPDATE if len(current_tracks) > 1 else EventState.ACTIVE,
                    event_id=best_match,
                    timestamp=now,
                    extra=event_extra,
                )
                events.append(event)
            elif current_tracks:
                event_id = f"{ActivityType.ZONE_INTRUSION.value}_{zone_id}_{camera_id}_{now:.0f}"
                person_details = []
                for track_id, d in current_intruders.items():
                    cx, cy = d.center
                    person_details.append({
                        "track_id": track_id,
                        "class_name": d.class_name,
                        "confidence": round(d.confidence, 3),
                        "bbox": [round(v, 1) for v in d.bbox],
                        "center": [round(cx, 1), round(cy, 1)],
                    })
                event_extra["persons"] = person_details
                active[event_id] = {
                    'start_time': now,
                    'tracks': current_tracks.copy(),
                    'extra': event_extra.copy(),
                }
                event = ActivityEvent(
                    activity_type=ActivityType.ZONE_INTRUSION,
                    track_ids=list(current_tracks),
                    camera_id=camera_id,
                    state=EventState.START,
                    event_id=event_id,
                    timestamp=now,
                    extra=event_extra
                )
                events.append(event)

        self._zone_intruders = all_intruders

        return events

    def _process_crowd(self, detections: list[Detection], camera_id: str, now: float, active_ids: Set[int]) -> list[ActivityEvent]:
        from core.config import CROWD_END_THRESHOLD, CROWD_GRACE_SECONDS, CROWD_COOLDOWN_SECONDS
        person_count = sum(1 for d in detections if d.class_name == 'person')

        events = []

        delta_time = now - getattr(self, '_last_crowd_time', 0)
        self._last_crowd_time = now

        if hasattr(self, '_crowd_cooldown_end') and now < self._crowd_cooldown_end:
            return events

        if not hasattr(self, '_crowd_state'):
            self._crowd_state = 'inactive'
            self._crowd_exit_timer = 0
            self._crowd_cooldown_end = 0

        if self._crowd_state == 'active':
            if person_count <= CROWD_END_THRESHOLD:
                self._crowd_exit_timer += delta_time
                if self._crowd_exit_timer >= CROWD_GRACE_SECONDS:
                    # END
                    event = ActivityEvent(
                        activity_type=ActivityType.CROWD,
                        track_ids=[],
                        camera_id=camera_id,
                        state=EventState.END,
                        event_id=f"crowd_end_{int(now*1000)}",
                        timestamp=now,
                        extra={'count': person_count}
                    )
                    events.append(event)
                    self._crowd_state = 'inactive'
                    self._crowd_cooldown_end = now + CROWD_COOLDOWN_SECONDS
                    self._crowd_exit_timer = 0
            else:
                self._crowd_exit_timer = 0  # Reset timer
        elif person_count >= self.crowd_threshold:
            # START
            event = ActivityEvent(
                activity_type=ActivityType.CROWD,
                track_ids=[],
                camera_id=camera_id,
                state=EventState.START,
                event_id=f"crowd_start_{int(now*1000)}",
                timestamp=now,
                extra={'count': person_count}
            )
            events.append(event)
            self._crowd_state = 'active'
            self._crowd_exit_timer = 0

        return events
