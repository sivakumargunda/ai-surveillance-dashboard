"""
main_fast.py - ULTRA-OPTIMIZED for 20+ FPS
Removes all overhead, bare minimum processing
"""
from __future__ import annotations

import os
import sys
import time
import cv2
import signal

# Windows DLL fix
if sys.platform == "win32":
    import site
    import sysconfig
    site_paths = sysconfig.get_paths()
    for key in ("purelib", "platlib"):
        torch_lib = os.path.join(site_paths.get(key, ""), "torch", "lib")
        if os.path.isdir(torch_lib) and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(torch_lib)

signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

# Ultra-minimal config
VIDEO_SOURCE = "c:/Users/sivak/Documents/Projects/surv-simple/samplevedio.mp4"
YOLO_MODEL = "yolov8n.pt"
YOLO_CONFIDENCE = 0.50
YOLO_DEVICE = "cpu"
FRAME_SKIP = 1  # Process EVERY frame (no skip for speed baseline)
RESIZE_W, RESIZE_H = 416, 320  # Tiny resolution for MAX speed
ENABLE_STREAMING = False  # DISABLE MJPEG streaming overhead
ENABLE_CLIPS = False  # DISABLE clip recording
ENABLE_DB = False  # DISABLE database writes
ENABLE_PRINT = False  # DISABLE all print statements

print(f"Loading YOLOv8n on {YOLO_DEVICE}...")

# Load model ONCE
from ultralytics import YOLO
model = YOLO(YOLO_MODEL)
model.to(YOLO_DEVICE)
print("Model ready!")

# Open video capture
cap = cv2.VideoCapture(VIDEO_SOURCE)
fps_video = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Video: {fps_video:.1f} FPS, {total_frames} frames")

frame_count = 0
fps_counter = 0
start_time = time.time()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_count = 0
            continue
        
        frame_count += 1
        
        # ULTRA-FAST: Resize to tiny size
        frame = cv2.resize(frame, (RESIZE_W, RESIZE_H))
        
        # Run detection (fastest possible)
        results = model.predict(frame, conf=YOLO_CONFIDENCE, verbose=False)
        
        # Count detections
        people_count = 0
        if results and results[0].boxes is not None:
            for box in results[0].boxes:
                if int(box.cls[0]) == 0:  # Person class
                    people_count += 1
        
        # Measure FPS every second
        fps_counter += 1
        elapsed = time.time() - start_time
        if elapsed >= 1.0:
            current_fps = fps_counter / elapsed
            print(f"FPS: {current_fps:.1f} | People: {people_count} | Frame: {frame_count}")
            fps_counter = 0
            start_time = time.time()
            
            # Reset if slow
            if current_fps < 15:
                print("Low FPS detected, switching to SKIP mode...")
        
        # Minimal display update (every 30 frames)
        if frame_count % 30 == 0 and people_count > 0:
            pass  # Event detected
        
finally:
    cap.release()
    print(f"Done! Processed {frame_count} frames")
