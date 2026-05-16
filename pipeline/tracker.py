"""
pipeline/tracker.py
Wraps deep-sort-realtime to assign persistent track IDs to detections.
"""

from __future__ import annotations

import numpy as np

from pipeline.detector import Detection, class_name_for_id


class Tracker:
    """
    Maintains object identities across frames.
    """

    def __init__(self, max_age: int = 15, n_init: int = 2) -> None:
        """ Initialize DeepSORT with optimized settings. """
        from deep_sort_realtime.deepsort_tracker import DeepSort

        self._ds = DeepSort(max_age=max_age, n_init=n_init)
        print(f"[Tracker] DeepSORT ready  max_age={max_age}  n_init={n_init}")

    def update(
        self,
        detections: list[Detection],
        frame: np.ndarray,
    ) -> list[Detection]:
        """
        Associate detections with existing tracks.
        """
        if not detections:
            self._ds.update_tracks([], frame=frame)
            return []

        ds_input = []
        for d in detections:
            x1, y1, x2, y2 = d.bbox
            ds_input.append(([x1, y1, x2 - x1, y2 - y1], d.confidence, d.class_id))

        tracks = self._ds.update_tracks(ds_input, frame=frame)

        tracked: list[Detection] = []
        for t in tracks:
            if not t.is_confirmed():
                continue
            l, top, r, b = t.to_ltrb()
            class_id = int(t.det_class) if t.det_class is not None else 0
            tracked.append(
                Detection(
                    bbox=(l, top, r, b),
                    confidence=t.det_conf or 0.0,
                    class_id=class_id,
                    class_name=class_name_for_id(class_id),
                    track_id=t.track_id,
                )
            )

        return tracked
