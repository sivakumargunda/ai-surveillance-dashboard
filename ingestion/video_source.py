"""
ingestion/video_source.py
─────────────────────────
Wraps OpenCV VideoCapture behind a simple iterator.
Accepts:
  - int        → webcam index  (e.g. 0)
  - str path   → .mp4 / .avi  (e.g. "video.mp4")
  - str URL    → RTSP stream   (e.g. "rtsp://192.168.1.1/stream")
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

import cv2
import numpy as np


@dataclass
class Frame:
    data: np.ndarray                          # HxWx3 BGR uint8
    camera_id: str
    frame_number: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def height(self) -> int:
        return self.data.shape[0]

    @property
    def width(self) -> int:
        return self.data.shape[1]


class VideoSource:
    """
    Iterates frames from any OpenCV-supported source.

    Usage:
        with VideoSource("video.mp4", camera_id="cam-1") as src:
            for frame in src:
                process(frame)
    """

    def __init__(
        self,
        source: str | int,
        camera_id: str = "cam-0",
        frame_skip: int = 1,
        loop: bool = False,          # loop file when it ends
        reconnect_delay: float = 3.0,
    ) -> None:
        self.source        = source
        self.camera_id     = camera_id
        self.frame_skip    = max(1, frame_skip)
        self.loop          = loop
        self.reconnect_delay = reconnect_delay

        self._cap: cv2.VideoCapture | None = None
        self._frame_num = 0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def open(self) -> None:
        src = int(self.source) if str(self.source).isdigit() else self.source
        self._cap = cv2.VideoCapture(src)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {self.source!r}")
        print(f"[VideoSource] opened -> {self.source}  "
              f"({self._cap.get(cv2.CAP_PROP_FRAME_WIDTH):.0f}x"
              f"{self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT):.0f} "
              f"@ {self._cap.get(cv2.CAP_PROP_FPS):.1f} fps)")

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "VideoSource":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ── Iteration ─────────────────────────────────────────────────────────────

    def __iter__(self):
        assert self._cap is not None, "Call open() before iterating"
        n = 0
        while True:
            ok, bgr = self._cap.read()

            if not ok:
                if self.loop:
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                # RTSP / live source: try to reconnect once
                if isinstance(self.source, str) and self.source.startswith("rtsp"):
                    print(f"[VideoSource] stream lost, reconnecting in {self.reconnect_delay}s...")
                    time.sleep(self.reconnect_delay)
                    self.close()
                    self.open()
                    continue
                break   # file ended, stop

            n += 1
            if n % self.frame_skip != 0:
                continue

            self._frame_num += 1
            yield Frame(
                data=bgr,
                camera_id=self.camera_id,
                frame_number=self._frame_num,
            )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @property
    def fps(self) -> float:
        if self._cap is None:
            return 0.0
        return float(self._cap.get(cv2.CAP_PROP_FPS)) or 25.0

    @property
    def total_frames(self) -> int:
        if self._cap is None:
            return 0
        return int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
