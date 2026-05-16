"""Multi Mobile Camera Surveillance - Fixed for Live Feed + Accurate Detection + Alerts"""

import os
import time
import threading
import cv2
import json
import base64
import urllib.request
import urllib.error
from ultralytics import YOLO
from core.config import YOLO_MODEL, YOLO_CONFIDENCE, YOLO_DEVICE, MULTI_CAM_URLS
from pipeline.detector import Detector
from pipeline.tracker import Tracker
from pipeline.activity import ActivityAnalyzer
from pipeline.alert import ConsoleAlerter, DatabaseAlerter
from pipeline.annotator_fixed import Annotator



print("Multi Mobile CCTV Fixed - Live Dashboard + Accurate Detection")
print("Cameras:", MULTI_CAM_URLS)

# Config
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

stop_event = threading.Event()

def _register_stream_frame(camera_id: str, frame):
    """Send frame to API for MJPEG streaming (like main.py)."""
    try:
        # Encode JPEG base64
        _, buffer = cv2.imencode('.jpg', frame)
        b64_image = base64.b64encode(buffer).decode('utf-8')
        
        payload = json.dumps({
            "camera_id": camera_id,
            "frame_b64": b64_image,
        }).encode("utf-8")
        
        request = urllib.request.Request(
            f"{API_BASE_URL}/register-frame",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=0.5):
            pass
    except Exception:
        pass  # Silently fail - optional feature

def cam_thread(cam_id, cam_url):
    cap = None
    frame_id = 0
    prev_time = 0
    detector = Detector(confidence=0.35)  # Lower for accuracy
    annotator = Annotator()

    tracker = Tracker()
    analyzer = ActivityAnalyzer()
    console_alerter = ConsoleAlerter()
    db_alerter = DatabaseAlerter()
    
    print(f"[START] {cam_id} <- {cam_url}")
    
    while not stop_event.is_set():
        if cap is None or not cap.isOpened():
            print(f"[CONNECT] {cam_id} trying...")
            cap = cv2.VideoCapture(cam_url)
            if not cap.isOpened():
                time.sleep(3)
                continue
        
        ret, frame = cap.read()
        if not ret:
            cap.release()
            cap = None
            time.sleep(1)
            continue
        
        frame_id += 1
        frame_small = cv2.resize(frame, (640, 480))  # YOLO input
        
        # Process every frame (no skip for accuracy)
        current_time = time.time()
        fps = 1 / (current_time - prev_time) if prev_time > 0 else 0
        prev_time = current_time
        
        # Detect
        detections = detector.detect(frame_small)
        confs = [round(d.confidence,2) for d in detections[:5]]
        print(f"[{cam_id}] Det: {len(detections)} persons (confs {confs})")
        
        tracked = tracker.update(detections, frame)
        events = analyzer.analyze(tracked, cam_id, frame.shape)
        
        # Alerts
        console_alerter.handle_all(events)
        db_alerter.handle_all(events)
        
        # Annotate
        zones = [{'rect': [int(c) for c in analyzer.zone_rect], 'name': 'Restricted Zone'}] if analyzer.zone_rect else None
        annotated = annotator.draw(frame, tracked, events, fps, zones)

        
        # Live feed to dashboard (every 2nd)
        if frame_id % 2 == 0:
            _register_stream_frame(cam_id, annotated)


        
        # Show window
        cv2.imshow(cam_id, annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    if cap:
        cap.release()
    print(f"[STOP] {cam_id}")

if __name__ == "__main__":
    try:
        threads = []
        for i, url in enumerate(MULTI_CAM_URLS):
            cam_id = f"cam-mobile-{i+1}"
            t = threading.Thread(target=cam_thread, args=(cam_id, url.strip()), daemon=True)
            t.start()
            threads.append(t)
        
        print("All cameras started. Dashboard: http://localhost:3000")
        print("Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_event.set()
        time.sleep(3)
    
    cv2.destroyAllWindows()
    print("Done!")

