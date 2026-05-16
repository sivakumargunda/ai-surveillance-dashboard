"""
pipeline/detector.py
────────────────────
Runs YOLOv8 inference on a frame and returns bounding-box detections.
Only detects persons (COCO class 0) by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
import sys
import sysconfig

import numpy as np

if sys.platform == "win32":
    site_paths = sysconfig.get_paths()
    for key in ("purelib", "platlib"):
        torch_lib = os.path.join(site_paths.get(key, ""), "torch", "lib")
        if os.path.isdir(torch_lib):
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(torch_lib)
            else:
                os.environ["PATH"] = torch_lib + os.pathsep + os.environ.get("PATH", "")
            break

from ultralytics import YOLO

from core.config import YOLO_CONFIDENCE, YOLO_DEVICE, YOLO_MODEL

_PERSON_CLASS_ID = 0
PERSON_CLASS_IDS = [_PERSON_CLASS_ID]
VEHICLE_CLASS_IDS = [2, 3, 5, 7]

COCO_CLASS_NAMES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus",
    "train", "truck", "boat", "traffic light", "fire hydrant", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag",
    "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana",
    "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza",
    "donut", "cake", "chair", "couch", "potted plant", "bed", "dining table",
    "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock",
    "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]


def class_name_for_id(class_id: int) -> str:
    if 0 <= class_id < len(COCO_CLASS_NAMES):
        return COCO_CLASS_NAMES[class_id]
    return f"class_{class_id}"


@dataclass
class Detection:
    """One bounding-box detection from the detector."""
    bbox: tuple[float, float, float, float]   # x1, y1, x2, y2  (pixels)
    confidence: float
    class_id: int
    class_name: str
    track_id: int | None = None               # filled in by Tracker

    # ── Derived helpers ───────────────────────────────────────────────────────

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @property
    def area(self) -> float:
        x1, y1, x2, y2 = self.bbox
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)

    def __repr__(self) -> str:
        tid = f" track={self.track_id}" if self.track_id is not None else ""
        return (f"Detection({self.class_name} conf={self.confidence:.2f} "
                f"bbox={tuple(round(v) for v in self.bbox)}{tid})")


class Detector:
    """
    Thin wrapper around Ultralytics YOLOv8.

    The model is loaded lazily on the first call to detect() so that
    the object can be created before GPU context is initialised.

    Example
    -------
    detector = Detector()
    detections = detector.detect(bgr_frame)
    """

    def __init__(
        self,
        model_path: str = YOLO_MODEL,
        confidence: float = YOLO_CONFIDENCE,
        device: str = YOLO_DEVICE,
        classes: list[int] | None = None,
    ) -> None:
        self.model_path = model_path
        self.confidence = confidence
        self.device     = device
        self.classes    = classes if classes is not None else PERSON_CLASS_IDS + VEHICLE_CLASS_IDS
        self._model: YOLO | None = None


    def _load(self) -> None:
        if self._model is None:
            self._model = YOLO(self.model_path)
# No .to(device) for ONNX; use predict device= kwarg
            print("[Detector] ready")

    # ── Public API ────────────────────────────────────────────────────────────

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """
        Run inference on a BGR numpy array.
        Returns a list of Detection objects (may be empty).
        """
        self._load()
        assert self._model is not None
        
        results = self._model.predict(
            frame,
            conf=self.confidence,
            classes=self.classes,
            verbose=False,
            device=self.device,
        )

        detections: list[Detection] = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls_id = int(box.cls[0])
                detections.append(Detection(
                    bbox=(x1, y1, x2, y2),
                    confidence=float(box.conf[0]),
                    class_id=cls_id,
                    class_name=r.names[cls_id],
                ))

        return detections
