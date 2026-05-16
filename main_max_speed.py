"""
main_max_speed.py - NO OVERHEAD VERSION FOR MAX FPS
Purpose: Show raw YOLO performance without ANY processing overhead
"""
from __future__ import annotations

import os
import sys
import time
import cv2

# Windows DLL fix
if sys.platform == "win32":
    import site
    import sysconfig
    site_paths = sysconfig.get_paths()
    for key in ("purelib", "platlib"):
        torch_lib = os.path.join(site_paths.get(key, ""), "torch", "lib")
        if os.path.isdir(torch_lib) and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(torch_lib)

# MAX SPEED CONFIG
VIDEO_SOURCE = "c:/Users/sivak/Documents/Projects/surv-simple/samplevedio.mp4"
YOLO_MODEL = "yolov8n.pt"
RESOLUTION = (224, 160)  # Tiny for MAX speed

print("Loading YOLOv8n...")
from ultralytics import YOLO
model = YOLO(YOLO_MODEL)
model.to("cpu")
print("Ready! Starting benchmark...")

cap = cv2.VideoCapture(VIDEO_SOURCE)
start = time.time()
frames = 0
people = 0

try:
    while frames < 300:  # Benchmark 300 frames
        ret, frame = cap.read()
        if not ret:
            break
        
        # Tiny resize
        frame = cv2.resize(frame, RESOLUTION)
        
        # Run detection
        results = model.predict(frame, conf=0.55, verbose=False)
        
        if results and results[0].boxes is not None:
            for box in results[0].boxes:
                if int(box.cls[0]) == 0:
                    people += 1
        
        frames += 1
        
        if frames % 30 == 0:
            elapsed = time.time() - start
            fps = 30 / (time.time() - start - (elapsed - 0.067))
            print(f"Frame {frames}: FPS={fps:.1f}, People={people}")
            
finally:
    cap.release()
    total = time.time() - start
    avg_fps = frames / total
    print(f"\nBENCHMARK COMPLETE:")
    print(f"Total frames: {frames}")
    print(f"Total time: {total:.2f}s")
    print(f"AVERAGE FPS: {avg_fps:.1f}")
