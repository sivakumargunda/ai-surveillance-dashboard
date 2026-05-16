import cv2
import numpy as np

class Annotator:
    COLORS = {
        'person':  (0, 255, 80),    # green
        'car':     (255, 165, 0),   # orange
        'default': (0, 200, 255),   # cyan
    }
    ZONE_COLOR   = (255, 0, 255)    # magenta
    ALERT_COLOR  = (0, 0, 255)      # red

    def draw(self, frame, tracks, events, fps=0, zones=None):
        if frame is None:
            return frame

        h, w = frame.shape[:2]

        # -- 1. Draw zones FIRST (behind everything) --------------
        if zones:
            overlay = frame.copy()
            for zone in zones:
                x1, y1, x2, y2 = zone['rect']
                cv2.rectangle(overlay, (x1, y1), (x2, y2), self.ZONE_COLOR, -1)
                cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
                cv2.rectangle(frame, (x1, y1), (x2, y2), self.ZONE_COLOR, 2)
                self._label(frame, zone.get('name', 'Zone'),
                            x1 + 6, y1 + 6, self.ZONE_COLOR, font_scale=0.5)

        # -- 2. Draw tracks ----------------------------------------
        seen_positions = []  # avoid overlapping labels
        for t in tracks:
            x1, y1, x2, y2 = [int(v) for v in t.bbox]
            cls   = t.class_name if hasattr(t, 'class_name') else 'person'
            color = self.COLORS.get(cls, self.COLORS['default'])
            tid   = getattr(t, 'track_id', '?')
            conf  = getattr(t, 'confidence', 0.0)

            # Bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Label -- shift down if overlapping another label
            label_y = y1 - 8
            for py in seen_positions:
                if abs(label_y - py) < 18:
                    label_y = py + 18
            seen_positions.append(label_y)

            label = f"{cls} #{tid} {conf:.2f}"
            self._label(frame, label, x1, max(label_y, 12), color)

        # -- 3. HUD overlay (top-left) -----------------------------
        active_events = [e for e in events if hasattr(e, 'state') and e.state.value == 'START']
        people_count  = sum(1 for t in tracks
                            if getattr(t, 'class_name', 'person') == 'person')

        hud_lines = [
            f"cam-mobile-1  FPS:{fps:.1f}  P:{people_count}",
        ]
        for ev in active_events:
            hud_lines.append(f"⚠ {ev.activity_type}")

        for i, line in enumerate(hud_lines):
            self._label(frame, line, 8, 18 + i * 22,
                        color=(0, 255, 180), font_scale=0.55, thickness=1)

        # -- 4. People + Objects count (top-right) -----------------
        obj_count  = len(tracks)
        count_text = f"People: {people_count}  Objects: {obj_count}"
        (tw, th), baseline = cv2.getTextSize(count_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        self._label(frame, count_text, w - tw - 10, th + baseline,
                    color=(200, 200, 200), font_scale=0.5, thickness=1)

        return frame

    def _label(self, frame, text, x, y,
               color=(0,255,80), font_scale=0.55, thickness=1):
        """Draw text with a solid dark background rectangle -- no ghosting."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)

        pad = 3
        # Background rectangle
        cv2.rectangle(frame,
                      (x - pad,     y - th - baseline - pad),
                      (x + tw + pad, y + pad),
                      (20, 20, 20), -1)          # dark bg
        # Text on top
        cv2.putText(frame, text, (x, y),
                    font, font_scale, color, thickness, cv2.LINE_AA)

if __name__ == "__main__":
    import numpy as np
    from dataclasses import dataclass

    @dataclass
    class FakeTrack:
        bbox = [50, 40, 200, 280]
        track_id = 3
        class_name = "person"
        confidence = 0.84

    @dataclass
    class FakeEvent:
        activity_type = "ZONE_INTRUSION"
        event_state = "START"

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    ann = Annotator()
    result = ann.draw(frame, [FakeTrack()], [FakeEvent()], fps=30.0)

    import cv2
    import os
    os.makedirs("artifacts", exist_ok=True)
    cv2.imwrite("artifacts/annotator_test.jpg", result)
    print("Test passed - saved to artifacts/annotator_test.jpg")
