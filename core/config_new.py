import os


VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "0")

# YOLO
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8n.pt")   # n/s/m/l/x
YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.45"))
YOLO_DEVICE = os.getenv("YOLO_DEVICE", "cpu")        # "cpu" or "0"

# Pipeline
FRAME_SKIP = int(os.getenv("FRAME_SKIP", "2"))       # process 1 in N frames
CROWD_THRESHOLD = int(os.getenv("CROWD_THRESHOLD", "6"))
CROWD_END_THRESHOLD = int(os.getenv("CROWD_END_THRESHOLD", "4"))
CROWD_GRACE_SECONDS = float(os.getenv("CROWD_GRACE_SECONDS", "5"))
CROWD_COOLDOWN_SECONDS = float(os.getenv("CROWD_COOLDOWN_SECONDS", "30"))
RUNNING_PIXELS_PER_FRAME = float(os.getenv("RUNNING_PIXELS_PER_FRAME", "18"))
FALLING_WIDE_RATIO = float(os.getenv("FALLING_WIDE_RATIO", "1.6"))
TAILGATING_DISTANCE_PX = float(os.getenv("TAILGATING_DISTANCE_PX", "30"))
TAILGATING_MIN_FRAMES = int(os.getenv("TAILGATING_MIN_FRAMES", "10"))
ABANDONED_OBJECT_SECONDS = int(os.getenv("ABANDONED_OBJECT_SECONDS", "10"))
ABANDONED_PERSON_DISTANCE_PX = float(os.getenv("ABANDONED_PERSON_DISTANCE_PX", "80"))
ILLEGAL_PARKING_SECONDS = int(os.getenv("ILLEGAL_PARKING_SECONDS", "15"))
SPEEDING_PIXELS_PER_FRAME = float(os.getenv("SPEEDING_PIXELS_PER_FRAME", "40"))
WRONG_WAY_MIN_MOVEMENT_PX = float(os.getenv("WRONG_WAY_MIN_MOVEMENT_PX", "12"))
ALERT_SCREENSHOT_DIR = os.getenv("ALERT_SCREENSHOT_DIR", "artifacts/alerts")
ALERT_SNAPSHOT_COOLDOWN_SECONDS = float(os.getenv("ALERT_SNAPSHOT_COOLDOWN_SECONDS", "30"))
ZONE_INTRUSION_RECT = os.getenv("ZONE_INTRUSION_RECT", "").strip()
ZONE_INTRUSION_DEFAULT_TOP_RIGHT_WIDTH_RATIO = float(
    os.getenv("ZONE_INTRUSION_DEFAULT_TOP_RIGHT_WIDTH_RATIO", "0.30")
)
ZONE_INTRUSION_DEFAULT_TOP_RIGHT_HEIGHT_RATIO = float(
    os.getenv("ZONE_INTRUSION_DEFAULT_TOP_RIGHT_HEIGHT_RATIO", "0.30")
)
ENABLE_ALERT_BEEP = os.getenv("ENABLE_ALERT_BEEP", "true").lower() == "true"

# Event Lifecycle
EVENT_MIN_DURATION = float(os.getenv("EVENT_MIN_DURATION", "10"))
EVENT_TRACK_IOU = float(os.getenv("EVENT_TRACK_IOU", "0.5"))

# Display
SHOW_WINDOW = os.getenv("SHOW_WINDOW", "true").lower() == "true"

# Clip recording
CLIP_DIR = os.getenv("CLIP_DIR", "artifacts/clips")
CLIP_FPS = int(os.getenv("CLIP_FPS", "10"))
CLIP_CODEC = os.getenv("CLIP_CODEC", "mp4v")
ENABLE_ZONE_CLIPS = os.getenv("ENABLE_ZONE_CLIPS", "true").lower() == "true"

# Fire/Smoke Detection
FIRE_CONFIDENCE = float(os.getenv("FIRE_CONFIDENCE", "0.6"))
SMOKE_CONFIDENCE = float(os.getenv("SMOKE_CONFIDENCE", "0.5"))
CONFIRM_FRAMES = int(os.getenv("CONFIRM_FRAMES", "5"))
ALERT_COOLDOWN = float(os.getenv("ALERT_COOLDOWN", "30"))
