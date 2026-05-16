from __future__ import annotations

import threading
import time
from typing import Optional

from core.camera_registry import CameraRegistry
from core.camera_worker import CameraWorker
from core.config import HOT_RELOAD_INTERVAL
from core.detection_engine import DetectionEngine


class CameraManager:
    def __init__(self) -> None:
        self.workers: dict[str, CameraWorker] = {}
        self.engine: Optional[DetectionEngine] = None
        self.registry = CameraRegistry()
        self._running = False

    def start(self) -> None:
        cameras = self.registry.load()
        for cam in cameras:
            if cam.get("enabled"):
                worker = CameraWorker(
                    cam["id"],
                    cam["url"],
                    rotate=cam.get("rotate", 0),
                )
                worker.start()
                self.workers[cam["id"]] = worker

        self.engine = DetectionEngine(self.workers)
        self.engine.start()
        self._running = True

        threading.Thread(target=self._hot_reload_loop, daemon=True).start()

    def add_camera(self, cam_id: str, url: str, rotate: int = 0) -> None:
        if cam_id in self.workers:
            return

        worker = CameraWorker(cam_id, url, rotate=rotate)
        worker.start()
        self.workers[cam_id] = worker
        if self.engine:
            self.engine.add_camera(cam_id, worker)

    def remove_camera(self, cam_id: str) -> None:
        if cam_id in self.workers:
            self.workers[cam_id].stop()
            del self.workers[cam_id]
        if self.engine:
            self.engine.remove_camera(cam_id)

    def get_stream_frame(self, cam_id: str):
        worker = self.workers.get(cam_id)
        return worker.get_stream_frame() if worker else None

    def get_status(self, cam_id: str) -> dict[str, object]:
        worker = self.workers.get(cam_id)
        state = self.engine.get_state(cam_id) if self.engine else {}
        return {
            "id": cam_id,
            "status": worker.status if worker else "offline",
            "fps": state.get("fps", 0),
            "people": state.get("people", 0),
            "events": state.get("events", []),
        }

    def get_all_statuses(self) -> dict[str, dict[str, object]]:
        return {cam_id: self.get_status(cam_id) for cam_id in self.workers}

    def get_event_queue(self):
        return self.engine.event_queue if self.engine else None

    def _hot_reload_loop(self) -> None:
        while self._running:
            time.sleep(HOT_RELOAD_INTERVAL)
            registry_cams = {c["id"] for c in self.registry.load() if c.get("enabled")}
            active_cams = set(self.workers.keys())

            for cam_id in registry_cams - active_cams:
                cam = self.registry.get(cam_id)
                if cam:
                    self.add_camera(cam_id, cam["url"], cam.get("rotate", 0))

            for cam_id in active_cams - registry_cams:
                self.remove_camera(cam_id)


camera_manager = CameraManager()
