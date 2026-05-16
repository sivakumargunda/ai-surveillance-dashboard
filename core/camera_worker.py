from __future__ import annotations

import threading
import time
from typing import Tuple

import cv2


class CameraWorker:
    def __init__(
        self,
        cam_id: str,
        url: str,
        rotate: int = 0,
        resolution: Tuple[int, int] = (640, 480),
    ) -> None:
        self.cam_id = cam_id
        self.url = url
        self.rotate = rotate
        self.resolution = resolution
        self.latest_frame = None
        self.stream_frame = None
        self.running = False
        self.status = "connecting"
        self.retry_count = 0
        self.max_retries = 5
        self._lock = threading.Lock()
        self._thread = None

    def start(self) -> None:
        self.running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False

    def _capture_loop(self) -> None:
        while self.running:
            cap = cv2.VideoCapture(self.url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

            if not cap.isOpened():
                self._handle_disconnect(cap)
                continue

            self.status = "online"
            self.retry_count = 0

            while self.running:
                ret, frame = cap.read()
                if not ret:
                    self._handle_disconnect(cap)
                    break

                if self.rotate == 90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                elif self.rotate == -90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                elif self.rotate == 180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)

                frame = cv2.resize(frame, self.resolution)

                with self._lock:
                    self.latest_frame = frame

            cap.release()

    def get_frame(self):
        with self._lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def set_stream_frame(self, frame) -> None:
        with self._lock:
            self.stream_frame = frame

    def get_stream_frame(self):
        with self._lock:
            if self.stream_frame is not None:
                return self.stream_frame.copy()
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def _handle_disconnect(self, cap) -> None:
        try:
            cap.release()
        except Exception:
            pass

        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self.status = "offline"
        else:
            self.status = "reconnecting"

        time.sleep(10)
