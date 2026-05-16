from __future__ import annotations

"""
main.py
Simplified surveillance pipeline with live streaming support.
"""

import os
import json
import signal
import site
import sys
import sysconfig
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    site_paths = sysconfig.get_paths()
    torch_lib_paths = []

    for key in ("purelib", "platlib"):
        torch_lib = os.path.join(site_paths.get(key, ""), "torch", "lib")
        if os.path.isdir(torch_lib):
            torch_lib_paths.append(torch_lib)

    user_site = site.getusersitepackages()
    torch_lib = os.path.join(user_site, "torch", "lib")
    if os.path.isdir(torch_lib):
        torch_lib_paths.append(torch_lib)

    for path in torch_lib_paths:
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(path)
            except Exception:
                pass

    if torch_lib_paths:
        os.environ["PATH"] = os.pathsep.join(torch_lib_paths) + os.pathsep + os.environ.get("PATH", "")

import cv2

import core.config as cfg
from ingestion.video_source import VideoSource
from pipeline.activity import ActivityAnalyzer, ActivityEvent, ActivityType, EventState
from pipeline.alert import ConsoleAlerter, DatabaseAlerter
from pipeline.annotator import draw_detections
from pipeline.detector import PERSON_CLASS_IDS, Detection, VEHICLE_CLASS_IDS
from pipeline.tracker import Tracker

# WebSocket imports for real-time push
try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False


_running = True


def _handle_sigint(*_) -> None:
    global _running
    print("\n[main] stopping ...")
    _running = False


signal.signal(signal.SIGINT, _handle_sigint)


class _FPSCounter:
    def __init__(self, window: int = 30) -> None:
        self._times: list[float] = []
        self._window = window

    def tick(self) -> float:
        now = time.perf_counter()
        self._times.append(now)
        if len(self._times) > self._window:
            self._times.pop(0)
        if len(self._times) < 2:
            return 0.0
        return (len(self._times) - 1) / (self._times[-1] - self._times[0])


def _save_alert_snapshot(
    frame,
    detections: list[Detection],
    events,
    analyzer: ActivityAnalyzer,
) -> list[Path]:
    if not events:
        return []

    output_dir = Path(cfg.ALERT_SCREENSHOT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated = draw_detections(frame, detections, events, zone_rect=analyzer.zone_rect)
    saved_paths: list[Path] = []

    for event in events:
        timestamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(event.timestamp))
        path = output_dir / f"{timestamp}_{event.activity_type}_{event.camera_id}.jpg"
        cv2.imwrite(str(path), annotated)
        saved_paths.append(path)

    return saved_paths


def _filter_snapshot_events(
    events: list[ActivityEvent],
    last_snapshot: dict[tuple[str, ActivityType], float],
) -> list[ActivityEvent]:
    if cfg.ALERT_SNAPSHOT_COOLDOWN_SECONDS <= 0:
        return events

    allowed: list[ActivityEvent] = []
    for event in events:
        key = (event.camera_id, event.activity_type)
        if event.timestamp - last_snapshot[key] < cfg.ALERT_SNAPSHOT_COOLDOWN_SECONDS:
            continue

        last_snapshot[key] = event.timestamp
        allowed.append(event)

    return allowed


def _register_stream_frame(camera_id: str, frame) -> None:
    """Register frame for MJPEG streaming via HTTP."""
    import base64
    import io
    
    try:
        # Encode frame as JPEG base64
        _, buffer = cv2.imencode('.jpg', frame)
        b64_image = base64.b64encode(buffer).decode('utf-8')
        
        # Send to API server
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
        payload = json.dumps({
            "camera_id": camera_id,
            "frame_b64": b64_image,
        }).encode("utf-8")
        
        request = urllib.request.Request(
            f"{api_base_url}/register-frame",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=0.5):
            pass
    except Exception:
        pass  # Silently fail - stream is optional


def _push_websocket_detection(people: int, vehicles: int, fps: float, tracked: int, detections: list, events: list) -> None:
    """Push detection data via WebSocket to dashboard."""
    if not WEBSOCKET_AVAILABLE:
        return
    
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
    
    # Build detections list
    detection_list = []
    for d in detections:
        detection_list.append({
            "track_id": d.track_id,
            "type": d.class_name,
            "confidence": round(d.confidence, 2),
            "bbox": list(d.bbox),
        })
    
    # Get event types
    event_types = [e.activity_type.value for e in events] if events else []
    
    payload = json.dumps({
        "type": "detections",
        "camera_id": "cam-0",
        "people_count": people,
        "vehicle_count": vehicles,
        "tracked": tracked,
        "fps": round(fps, 1),
        "detections": detection_list,
        "events": event_types,
        "timestamp": datetime.utcnow().isoformat(),
    }).encode("utf-8")
    
    try:
        ws_url = api_base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws = websocket.create_connection(f"{ws_url}/ws", timeout=1)
        ws.send(payload)
        ws.close()
    except Exception:
        pass


def _send_live_stats(people: int, vehicles: int, fps: float, tracked: int) -> None:
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
    payload = json.dumps({
        "people": people,
        "vehicles": vehicles,
        "fps": round(fps, 1),
        "tracked": tracked,
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{api_base_url}/live-stats",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=1):
            pass
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"[live-stats] failed to update API: {exc}")


def _clip_filename_for_event(event_id: str) -> str:
    safe_event_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in event_id)
    return f"zone_intrusion_{safe_event_id}.mp4"


def main() -> None:
    print("=" * 60)
    print(" Surveillance System - enhanced edition")
    print("=" * 60)
    print(f"  source  : {cfg.VIDEO_SOURCE}")
    print(f"  model   : {cfg.YOLO_MODEL}  conf={cfg.YOLO_CONFIDENCE}  device={cfg.YOLO_DEVICE}")
    print(f"  skip    : every {cfg.FRAME_SKIP} frames")
    print(f"  window  : {'yes' if cfg.SHOW_WINDOW else 'no'}")
    print(f"  zone    : {cfg.ZONE_INTRUSION_RECT or 'top-right auto (default)'}")
    print(f"  alerts  : database enabled")
    print(f"  stream  : MJPEG enabled at /stream/{{camera_id}}")
    print("=" * 60)

    source = VideoSource(cfg.VIDEO_SOURCE, camera_id="cam-0", frame_skip=cfg.FRAME_SKIP, loop=True)
    from pipeline.detector import Detector

    detector = Detector()
    tracker = Tracker()
    analyzer = ActivityAnalyzer()
    console_alerter = ConsoleAlerter()
    db_alerter = DatabaseAlerter()
    fps_ctr = _FPSCounter()
    last_snapshot: dict[tuple[str, ActivityType], float] = defaultdict(float)
    active_clip_writers: dict[str, dict[str, object]] = {}
    from core.config import ENABLE_ZONE_CLIPS, CLIP_DIR, CLIP_FPS, CLIP_CODEC

    with source:
        for frame in source:
            if not _running:
                break

            detections = detector.detect(frame.data)
            tracked = tracker.update(detections, frame.data)
            events = analyzer.analyze(
                tracked,
                camera_id=frame.camera_id,
                frame_shape=frame.data.shape,
            )
            emitted = console_alerter.handle_all(events)

            # Register annotated frame for MJPEG streaming (every 2 frames)
            if frame.frame_number % 2 == 0:
                annotated = draw_detections(frame.data, tracked, emitted, zone_rect=analyzer.zone_rect)
                _register_stream_frame(frame.camera_id, annotated)

            # Clip recording for zone intrusion: START opens a writer, every frame
            # is recorded while active, END closes it and attaches clip_path.
            if ENABLE_ZONE_CLIPS:
                clip_dir = Path(CLIP_DIR)
                clip_dir.mkdir(parents=True, exist_ok=True)

                for event in events:
                    if event.activity_type != ActivityType.ZONE_INTRUSION or event.state != EventState.START:
                        continue

                    event_id = event.event_id
                    if event_id in active_clip_writers:
                        continue

                    fourcc = cv2.VideoWriter_fourcc(*CLIP_CODEC)
                    h, w = frame.data.shape[:2]
                    clip_path = clip_dir / _clip_filename_for_event(event_id)
                    writer = cv2.VideoWriter(str(clip_path), fourcc, CLIP_FPS, (w, h))
                    if writer.isOpened():
                        active_clip_writers[event_id] = {
                            "writer": writer,
                            "path": clip_path,
                        }
                        print(f"[clip] started {clip_path}")
                    else:
                        writer.release()
                        print(f"[clip] failed to start writer for {clip_path}")

                for clip in list(active_clip_writers.values()):
                    writer = clip["writer"]
                    writer.write(frame.data)

                for event in events:
                    if event.activity_type != ActivityType.ZONE_INTRUSION or event.state != EventState.END:
                        continue

                    clip = active_clip_writers.pop(event.event_id, None)
                    if clip is None:
                        continue

                    writer = clip["writer"]
                    clip_path = clip["path"]
                    writer.release()
                    event.extra["clip_path"] = str(clip_path)
                    print(f"[clip] saved {clip_path}")

            persistence_events = list(emitted)
            for event in events:
                if (
                    event.activity_type == ActivityType.ZONE_INTRUSION
                    and event.state == EventState.END
                    and event.extra.get("clip_path")
                    and event not in persistence_events
                ):
                    persistence_events.append(event)

            snapshot_events = _filter_snapshot_events(emitted, last_snapshot)
            snapshot_paths_by_event_id: dict[str, str] = {}
            if snapshot_events:
                saved = _save_alert_snapshot(frame.data, tracked, snapshot_events, analyzer)
                for path, event in zip(saved, snapshot_events, strict=True):
                    print(f"[snapshot] saved {path}")
                    snapshot_paths_by_event_id[event.event_id] = str(path)

            for event in persistence_events:
                db_alerter.handle(event, snapshot_paths_by_event_id.get(event.event_id))

            if cfg.SHOW_WINDOW:
                annotated = draw_detections(frame.data, tracked, emitted, zone_rect=analyzer.zone_rect)
                fps = fps_ctr.tick()
                cv2.putText(
                    annotated,
                    f"FPS: {fps:.1f}",
                    (12, annotated.shape[0] - 12),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (160, 160, 160),
                    1,
                )
                cv2.imshow("Surveillance", annotated)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
            else:
                fps_ctr.tick()

            if frame.frame_number % 30 == 0:
                fps = fps_ctr.tick()
                people = sum(1 for detection in tracked if detection.class_id in PERSON_CLASS_IDS)
                vehicles = sum(1 for detection in tracked if detection.class_id in VEHICLE_CLASS_IDS)
                print(
                    f"[frame {frame.frame_number:>6}]  "
                    f"people={people:>2}  "
                    f"vehicles={vehicles:>2}  "
                    f"tracked={len(tracked):>2}  "
                    f"fps={fps:.1f}  "
                    f"events={len(events)}"
                )
                _send_live_stats(people, vehicles, fps, len(tracked))
                _push_websocket_detection(people, vehicles, fps, len(tracked), tracked, events)

    for clip in active_clip_writers.values():
        writer = clip["writer"]
        writer.release()

    cv2.destroyAllWindows()
    print("[main] done.")


if __name__ == "__main__":
    main()
