import cv2
import numpy as np


class Annotator:
    COLORS = {
        "person": (0, 255, 80),
        "car": (255, 165, 0),
        "default": (0, 200, 255),
    }
    ZONE_COLOR = (255, 0, 255)
    ALERT_COLOR = (0, 0, 255)

    def draw(self, frame, tracks, events, fps=0, zones=None):
        if frame is None:
            return frame

        h, w = frame.shape[:2]

        # Draw zones first so labels and tracks stay readable.
        if zones:
            overlay = frame.copy()
            for zone in zones:
                points = zone.get("points")
                if points and len(points) >= 3:
                    polygon = np.array(points, dtype=np.int32)
                    cv2.fillPoly(overlay, [polygon], self.ZONE_COLOR)
                    cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
                    cv2.polylines(frame, [polygon], True, self.ZONE_COLOR, 2)
                    label_x, label_y = polygon[0].tolist()
                else:
                    x1, y1, x2, y2 = zone["rect"]
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), self.ZONE_COLOR, -1)
                    cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), self.ZONE_COLOR, 2)
                    label_x, label_y = x1, y1
                self._label(
                    frame,
                    zone.get("zone_name") or zone.get("name", "Zone"),
                    int(label_x) + 6,
                    int(label_y) + 18,
                    self.ZONE_COLOR,
                    font_scale=0.5,
                )

        seen_positions = []
        for t in tracks:
            x1, y1, x2, y2 = [int(v) for v in t.bbox]
            cls = t.class_name if hasattr(t, "class_name") else "person"
            color = self.COLORS.get(cls, self.COLORS["default"])
            tid = getattr(t, "track_id", "?")
            conf = getattr(t, "confidence", 0.0)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label_y = y1 - 8
            for py in seen_positions:
                if abs(label_y - py) < 18:
                    label_y = py + 18
            seen_positions.append(label_y)

            label = f"{cls} #{tid} {conf:.2f}"
            self._label(frame, label, x1, max(label_y, 12), color)

        active_events = [e for e in events if self._event_state(e) == "start"]
        people_count = sum(
            1 for t in tracks if getattr(t, "class_name", "person") == "person"
        )

        hud_lines = [
            f"cam-mobile-1  FPS:{fps:.1f}  P:{people_count}",
        ]
        for ev in active_events:
            hud_lines.append(f"! {self._event_type(ev)}")

        for i, line in enumerate(hud_lines):
            self._label(
                frame,
                line,
                8,
                18 + i * 22,
                color=(0, 255, 180),
                font_scale=0.55,
                thickness=1,
            )

        obj_count = len(tracks)
        count_text = f"People: {people_count}  Objects: {obj_count}"
        (tw, th), baseline = cv2.getTextSize(
            count_text,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            1,
        )
        self._label(
            frame,
            count_text,
            w - tw - 10,
            th + baseline,
            color=(200, 200, 200),
            font_scale=0.5,
            thickness=1,
        )

        return frame

    def _event_state(self, event):
        state = getattr(event, "state", getattr(event, "event_state", ""))
        value = getattr(state, "value", state)
        return str(value).lower()

    def _event_type(self, event):
        activity_type = getattr(event, "activity_type", "")
        return getattr(activity_type, "value", activity_type)

    def _label(self, frame, text, x, y, color=(0, 255, 80), font_scale=0.55, thickness=1):
        """Draw text with a solid dark background rectangle -- no ghosting."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)

        pad = 3
        cv2.rectangle(
            frame,
            (x - pad, y - th - baseline - pad),
            (x + tw + pad, y + pad),
            (20, 20, 20),
            -1,
        )
        cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)


def draw_detections(frame, tracks, events=None, fps=0, zone_rect=None):
    zones = None
    if zone_rect:
        zones = [{"rect": [int(c) for c in zone_rect], "name": "Restricted Zone"}]
    return Annotator().draw(frame.copy(), tracks, events or [], fps, zones)
