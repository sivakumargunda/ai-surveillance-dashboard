"""
main_20fps.py - ACHIEVES 20+ FPS by skipping YOLO detection
Detection runs every 5th frame, but video plays at full speed
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

VIDEO_SOURCE = "c:/Users/sivak/Documents/Projects/surv-simple/samplevedio.mp4"
YOLO_MODEL = "yolov8n.pt"
DETECT_EVERY = 5  # Run detection every 5th frame only
RESOLUTION = (320, 240)  # Small for speed

print("Loading YOLOv8n...")
from ultralytics import YOLO
model = YOLO(YOLO_MODEL)
model.to("cpu")
print("Ready!")

cap = cv2.VideoCapture(VIDEO_SOURCE)
video_fps = cap.get(cv2.CAP_PROP_FPS)
print(f"Video FPS: {video_fps}")

# Last known detections (reused for skipped frames)
last_boxes = []
last_people = 0
frame_count = 0
detect_count = 0
start = time.time()

try:
    while frame_count < 600:  # Run 10 seconds worth
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        frame_count += 1
        
        # Small resize for speed
        frame_small = cv2.resize(frame, RESOLUTION)
        
        # Only run YOLO every 5th frame
        if frame_count % DETECT_EVERY == 0:
            results = model.predict(frame_small, conf=0.55, verbose=False)
            last_boxes = []
            last_people = 0
            if results and results[0].boxes is not None:
                for box in results[0].boxes:
                    if int(box.cls[0]) == 0:
                        last_people += 1
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        last_boxes.append((int(x1), int(y1), int(x2), int(y2)))
            detect_count += 1
        
        # Draw last known boxes (reuse for skipped frames)
        # NOTE: This benchmarking script is intentionally raw/low-overhead.
        for x1, y1, x2, y2 in last_boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)


        
        # Show every 30 frames
        if frame_count % 30 == 0:
            cv2.putText(frame, f"FPS: {video_fps:.0f} | People: {last_people}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("20+ FPS Detection", frame)
            cv2.waitKey(1)
            
            elapsed = time.time() - start
            current_fps = frame_count / elapsed
            print(f"Frame {frame_count} ({current_fps:.1f} FPS actual, {detect_count} detections)")

finally:
    cap.release()
    cv2.destroyAllWindows()
    total = time.time() - start
    avg_fps = frame_count / total
    print(f"\nRESULT: {avg_fps:.1f} FPS average (video plays at {video_fps:.0f})")
    print(f"Detections performed: {detect_count} ({detect_count*100/frame_count:.0f}% of frames)")
