 time
import numpy as np
from ultralytics import YOLO
from core.config import YOLO_MODEL, YOLO_CONFIDENCE, YOLO_DEVICE
from pipeline.tracker import Tracker
from pipeline.detector import Detector
from pipeline.activity import ActivityAnalyzer
from pipeline.alert import ConsoleAlerter, DatabaseAlerter
from pipeline.annotator_fixed import Annotator
import os
import json
import base64
import urllib.request
import urllib.error

# Config
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

from core.config import MULTI_CAM_URLS
# Use first mobile cam
STREAM_URL = MULTI_CAM_URLS[0]

print("Mobile CCTV Surveillance Starting...")
print("Stream:", STREAM_URL)
print("Press ESC to stop")

detector = Detector()
tracker = Tracker()
analyzer = ActivityAnalyzer()
console_alerter = ConsoleAlerter()
db_alerter = DatabaseAlerter()

frame_id = 0
prev_time = 0
cap = None

try:
    while True:
        # RECONNECT LOGIC
        if cap is None or not cap.isOpened():
            print(f"Connecting to {STREAM_URL}...")
            cap = cv2.VideoCapture(STREAM_URL)
            if not cap.isOpened():
                print("Failed to connect, retrying in 3s...")
                time.sleep(3)
                continue
            else:
                print("Camera connected!")
        
        ret, frame = cap.read()
        if not ret:
            print("No frame, reconnecting...")
            cap.release()
            cap = None
            time.sleep(1)
            continue
        
        frame_id += 1
        
        # PERFORMANCE: Resize + frame skip
        frame_small = cv2.resize(frame, (640, 480))
        if frame_id % 2 != 0:
            continue
        
        # FPS
        current_time = time.time()
        fps = 1 / (current_time - prev_time) if prev_time > 0 else 0
        prev_time = current_time
        
        # PIPELINE
        detections = detector.detect(frame_small)
        tracked = tracker.update(detections, frame)
        events = analyzer.analyze(tracked, "cam-mobile-1", frame.shape)
        
        # Alerts
        console_alerter.handle_all(events)
        db_alerter.handle_all(events)
        
        # Annotate
        zones = [{'rect': [int(c) for c in analyzer.zone_rect], 'name': 'Restricted Zone'}] if analyzer.zone_rect else None
        annotator = Annotator()
        frame_annotated = annotator.draw(frame, tracked, events, fps, zones)
        annotated = frame_annotated

        
        # Resize for stream efficiency
        annotated_resized = cv2.resize(annotated, (640, 480))
        
        # Overlay on resized
        cv2.putText(annotated_resized, f"FPS: {fps:.1f}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_resized, f"People: {sum(1 for t in tracked if t.class_id == 0)}", (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        # Register stream frame every 2nd processed frame for dashboard
        if frame_id % 4 == 0:
            try:
                _, buffer = cv2.imencode('.jpg', annotated_resized)
                b64_image = base64.b64encode(buffer).decode('utf-8')
                
                payload = json.dumps({
                    "camera_id": "cam-mobile-1",
                    "frame_b64": b64_image,
                }).encode("utf-8")
                
                request = urllib.request.Request(
                    f"{API_BASE_URL}/register-frame",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                response = urllib.request.urlopen(request, timeout=1.0)
                print(f"Stream frame registered ({response.status})")
            except urllib.error.URLError as e:
                if hasattr(e, 'reason'):
                    print(f"Stream reg network error: {e.reason}")
                elif hasattr(e, 'code'):
                    print(f"Stream reg HTTP error: {e.code}")
            except Exception as e:
                print(f"Stream reg failed: {e}")
        
        # HUD/count now in Annotator.draw(), manual overlays removed

        
        cv2.imshow("Mobile CCTV", annotated)
        
        if cv2.waitKey(1) == 27:  # ESC
            break
            
except KeyboardInterrupt:
    print("Stopped by user")

finally:
    if cap:
        cap.release()
    cv2.destroyAllWindows()
    print("Done!")
