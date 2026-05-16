from __future__ import annotations

import queue
import threading
import time
import json
from datetime import datetime

from ultralytics import YOLO

from core.config import DETECT_SKIP, IMGSZ, MODEL, YOLO_CONF
from core.models import SessionLocal, Zone
from pipeline.activity import ActivityAnalyzer
from pipeline.alert import DatabaseAlerter
from pipeline.annotator import Annotator
from pipeline.detector import Detection, class_name_for_id
from pipeline.tracker import Tracker


class DetectionEngine:
    def __init__(self, cameras: dict[str, "CameraWorker"]) -> None:
        self.cameras = cameras
        self.model = YOLO(MODEL)
        self.model.overrides["verbose"] = False
        self.trackers: dict[str, Tracker] = {}
        self.analyzers: dict[str, ActivityAnalyzer] = {}
        self.alerters: dict[str, DatabaseAlerter] = {}
        self.annotator = Annotator()
        self.fps_counters: dict[str, dict[str, float]] = {}
        self.running = False
        self.camera_states: dict[str, dict[str, object]] = {}
        self.event_queue: queue.Queue[dict] = queue.Queue()
        self._last_detections: dict[str, list[Detection]] = {}
        self._zone_cache: dict[str, dict[str, object]] = {}
        self._last_detector_error: dict[str, str] = {}

        for cam_id, worker in cameras.items():
            self.trackers[cam_id] = Tracker()
            self.analyzers[cam_id] = ActivityAnalyzer()
            self.alerters[cam_id] = DatabaseAlerter()
            self.camera_states[cam_id] = {"people": 0, "events": [], "fps": 0}

    def start(self) -> None:
        self.running = True
        thread = threading.Thread(target=self._detection_loop, daemon=True)
        thread.start()

    def add_camera(self, cam_id: str, worker: "CameraWorker") -> None:
        self.cameras[cam_id] = worker
        self.trackers[cam_id] = Tracker()
        self.analyzers[cam_id] = ActivityAnalyzer()
        self.alerters[cam_id] = DatabaseAlerter()
        self.camera_states[cam_id] = {"people": 0, "events": [], "fps": 0}

    def remove_camera(self, cam_id: str) -> None:
        self.cameras.pop(cam_id, None)
        self.trackers.pop(cam_id, None)
        self.analyzers.pop(cam_id, None)
        self.alerters.pop(cam_id, None)
        self.camera_states.pop(cam_id, None)
        self._last_detections.pop(cam_id, None)
        self.fps_counters.pop(cam_id, None)
        self._zone_cache.pop(cam_id, None)

    def _detection_loop(self) -> None:
        detect_counter: dict[str, int] = {}

        while self.running:
            for cam_id, worker in list(self.cameras.items()):
                if worker.status != "online":
                    continue

                frame = worker.get_frame()
                if frame is None:
                    continue

                detect_counter.setdefault(cam_id, 0)
                detect_counter[cam_id] += 1

                if detect_counter[cam_id] % DETECT_SKIP == 0:
                    try:
                        results = self.model(frame, imgsz=IMGSZ, conf=YOLO_CONF,
                                             classes=[0, 2, 3, 5, 7], verbose=False)[0]
                        detections = self._parse_results(results)
                        self._last_detections[cam_id] = detections
                        self._last_detector_error.pop(cam_id, None)
                    except Exception as exc:
                        message = str(exc)
                        if self._last_detector_error.get(cam_id) != message:
                            print(f"[DetectionEngine] detector error camera={cam_id}: {message}")
                        self._last_detector_error[cam_id] = message
                        detections = self._last_detections.get(cam_id, [])
                else:
                    detections = self._last_detections.get(cam_id, [])

                tracks = self.trackers[cam_id].update(detections, frame)
                zones = self._get_zones(cam_id)
                events = self.analyzers[cam_id].analyze(tracks, cam_id, frame.shape, zones=zones)

                for event in events:
                    self.alerters[cam_id].handle(event)
                    self.event_queue.put({
                        "camera_id": cam_id,
                        "event": event.activity_type.value if hasattr(event.activity_type, 'value') else str(event.activity_type),
                        "state": event.state.value if hasattr(event.state, 'value') else str(event.state),
                        "people": sum(1 for t in tracks if getattr(t, 'class_name', 'person') == 'person'),
                        "timestamp": datetime.now().isoformat(),
                    })

                people = sum(1 for t in tracks if getattr(t, 'class_name', 'person') == 'person')
                self._update_fps(cam_id)
                self.camera_states[cam_id] = {
                    "people": people,
                    "events": [e.activity_type.value for e in events if getattr(e, 'state', None) and getattr(e.state, 'value', str(e.state)) == 'start'],
                    "fps": self.fps_counters.get(cam_id, {}).get("fps", 0),
                }

                draw_zones = zones or self._default_zone_for_analyzer(cam_id)
                annotated = self.annotator.draw(frame.copy(), tracks, events, self.camera_states[cam_id]["fps"], draw_zones)
                worker.set_stream_frame(annotated)

            time.sleep(0.01)

    def _parse_results(self, results) -> list[Detection]:
        detections: list[Detection] = []
        if getattr(results, 'boxes', None) is None:
            return detections

        for box in results.boxes:
            bbox = box.xyxy[0].tolist()
            cls_id = int(box.cls[0])
            detections.append(Detection(
                bbox=(bbox[0], bbox[1], bbox[2], bbox[3]),
                confidence=float(box.conf[0]),
                class_id=cls_id,
                class_name=results.names[cls_id] if getattr(results, 'names', None) else str(cls_id),
            ))

        return detections

    def _update_fps(self, cam_id: str) -> None:
        now = time.time()
        counter = self.fps_counters.setdefault(cam_id, {"count": 0, "fps": 0.0, "t": now})
        counter["count"] += 1
        elapsed = now - counter["t"]
        if elapsed >= 1.0:
            counter["fps"] = round(counter["count"] / elapsed, 1)
            counter["count"] = 0
            counter["t"] = now

    def _get_zones(self, cam_id: str) -> list[dict]:
        now = time.time()
        cached = self._zone_cache.get(cam_id)
        if cached and now - cached["loaded_at"] < 2.0:
            return cached["zones"]

        zones: list[dict] = []
        db = SessionLocal()
        try:
            rows = db.query(Zone).filter(Zone.camera_id == cam_id).all()
            for row in rows:
                try:
                    points = json.loads(row.points) if row.points else []
                except json.JSONDecodeError:
                    points = []
                zones.append({
                    "id": row.id,
                    "camera_id": row.camera_id,
                    "zone_name": row.zone_name,
                    "zone_type": row.zone_type,
                    "points": points,
                })
        finally:
            db.close()

        self._zone_cache[cam_id] = {"loaded_at": now, "zones": zones}
        return zones

    def _default_zone_for_analyzer(self, cam_id: str) -> list[dict]:
        analyzer = self.analyzers.get(cam_id)
        zone_rect = getattr(analyzer, "zone_rect", None)
        if not zone_rect:
            return []
        return [{"rect": [int(c) for c in zone_rect], "name": "Restricted Zone"}]

    def get_state(self, cam_id: str) -> dict[str, object]:
        return self.camera_states.get(cam_id, {"people": 0, "events": [], "fps": 0})

    def get_all_states(self) -> dict[str, dict[str, object]]:
        return dict(self.camera_states)
