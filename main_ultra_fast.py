"""
main_ultra_fast.py - ULTRA-FAST THREADED PIPELINE FOR 20+ FPS
Thread 1: Capture frames
Thread 2: Detection only (no other processing)
Thread 3: Display/Output only
"""
from __future__ import annotations

import os
import sys
import time
import threading
import queue
import cv2
from types import SimpleNamespace

# Windows DLL fix
if sys.platform == "win32":
    import site
    import sysconfig
    site_paths = sysconfig.get_paths()
    for key in ("purelib", "platlib"):
        torch_lib = os.path.join(site_paths.get(key, ""), "torch", "lib")
        if os.path.isdir(torch_lib) and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(torch_lib)

# =============================================================
# CONFIG - OPTIMIZED FOR MAXIMUM SPEED
# =============================================================
VIDEO_SOURCE = "c:/Users/sivak/Documents/Projects/surv-simple/samplevedio.mp4"
YOLO_MODEL = "yolov8n.pt"
YOLO_CONFIDENCE = 0.55
YOLO_DEVICE = "cpu"
RESIZE_W, RESIZE_H = 320, 240  # Very small for MAX speed
MAX_QUEUE_SIZE = 2  # Small queue = less memory

print("=" * 60)
print("ULTRA-FAST THREADED PIPELINE (20+ FPS TARGET)")
print("=" * 60)

# =============================================================
# LOAD MODEL ONCE (before threading)
# =============================================================
from ultralytics import YOLO
from pipeline.annotator import Annotator
print("Loading YOLO model...")
yolo = YOLO(YOLO_MODEL)
yolo.to(YOLO_DEVICE)
print("Model loaded!")

# =============================================================
# QUEUES FOR THREADING
# =============================================================
frame_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
result_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
stop_event = threading.Event()

# =============================================================
# THREAD 1: CAPTURE (reads video, puts raw frames in queue)
# =============================================================
def capture_thread():
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    frame_id = 0
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_id = 0
            continue
        
        frame_id += 1
        frame_small = cv2.resize(frame, (RESIZE_W, RESIZE_H))
        
        try:
            frame_queue.put((frame_id, frame_small, frame), timeout=0.1)
        except queue.Full:
            pass
    
    cap.release()

# =============================================================
# THREAD 2: DETECTION (runs YOLO, puts results in queue)
# =============================================================
def detection_thread():
    while not stop_event.is_set():
        try:
            frame_id, frame_small, frame_orig = frame_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        
        # FAST YOLO inference
        results = yolo.predict(frame_small, conf=YOLO_CONFIDENCE, verbose=False)
        
        # Count people
        people = 0
        boxes = []
        if results and results[0].boxes is not None:
            for box in results[0].boxes:
                cls = int(box.cls[0])
                if cls == 0:  # Person
                    people += 1
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    boxes.append((x1, y1, x2, y2))
        
        try:
            result_queue.put((frame_id, people, boxes, frame_orig), timeout=0.1)
        except queue.Full:
            pass

# =============================================================
# THREAD 3: OUTPUT (display FPS and counts)
# =============================================================
def output_thread():
    annotator = Annotator()
    fps = 0
    frame_count = 0
    last_time = time.time()
    people_total = 0
    
    while not stop_event.is_set():
        try:
            frame_id, people, boxes, frame_orig = result_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        
        frame_count += 1
        people_total += people
        
        # Calculate FPS every 30 frames
        if frame_count % 30 == 0:
            now = time.time()
            elapsed = now - last_time
            fps = 30 / elapsed if elapsed > 0 else 0
            last_time = now
            print(f"FPS: {fps:.1f} | People: {people} | Total: {frame_count} | Avg: {people_total/frame_count:.1f}")
        
        tracks = [
            SimpleNamespace(
                bbox=(x1, y1, x2, y2),
                track_id=i + 1,
                class_name="person",
                confidence=0.0,
            )
            for i, (x1, y1, x2, y2) in enumerate(boxes)
        ]
        annotated = annotator.draw(frame_orig.copy(), tracks, [], fps)
        
        # Show every 30 frames
        if frame_count % 30 == 0:
            cv2.imshow("Fast Detection", annotated)
            cv2.waitKey(1)

# =============================================================
# MAIN - START ALL THREADS
# =============================================================
try:
    print("Starting threads...")
    t1 = threading.Thread(target=capture_thread, daemon=True)
    t2 = threading.Thread(target=detection_thread, daemon=True)
    t3 = threading.Thread(target=output_thread, daemon=True)
    
    t1.start()
    t2.start()
    t3.start()
    
    print("Running! Press Ctrl+C to stop...")
    
    while True:
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\nStopping...")
    stop_event.set()
    time.sleep(0.5)
    cv2.destroyAllWindows()
    print("Done!")
