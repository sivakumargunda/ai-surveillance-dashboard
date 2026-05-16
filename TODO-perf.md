# Performance Optimization TODO for main_mobile_multi_fixed.py

## Issues Fixed So Far:
- [x] IndentationError in detector.py
- [x] ONNX .to(device) error

## Pending Perf Fixes:
- [ ] Thread limits (torch, cv2, OMP)
- [ ] Confidence = 0.40 (no ghosts)
- [ ] Add DETECT_SKIP_FRAMES = 4 logic
- [ ] Pass imgsz=320 to YOLO predict
- [ ] api.py: JPEG quality = 50
- [ ] Rerun script with good FPS/conf

Status: Starting perf edits...
