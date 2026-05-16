# Surveillance System - Product Upgrade Plan

## Phase 1: Implement Live Camera Feed with MJPEG Stream

### Step 1: Add MJPEG Stream Endpoint
- **File**: `api.py`
- **New Endpoint**: `GET /stream/{camera_id}` - ReturnsMJPEG multipart stream
- **Implementation**:
  - Create a generator that yields frames with bounding boxes
  - Use OpenCV to encode frames as JPEG
  - Yield in multipart/x-mixed-replace format

### Step 2: Create Stream Manager
- **File**: `api.py`
- **Purpose**: Manage active streams for different cameras
- **Methods**:
  - `register_frame(camera_id, frame)` - Register latest annotated frame
  - `get_frame(camera_id)` - Get current frame for streaming

## Phase 2: Implement Real-time WebSocket Push

### Step 3: Enhance WebSocket to Push Updates
- **File**: `api.py`
- **Current**: Uses `ConnectionManager` for client connections
- **Upgrade**: Add `broadcast_detection()` method
- **Data format**:
```json
{
    "type": "detections",
    "camera_id": "cam-0",
    "people_count": 8,
    "tracked_count": 5,
    "fps": 14.2,
    "detections": [
        {"track_id": 1, "type": "person", "confidence": 0.76, "bbox": [x1, y1, x2, y2]},
        {"track_id": 2, "type": "person", "confidence": 0.48, "bbox": [x1, y1, x2, y2]}
    ],
    "events": ["crowd", "zone_intrusion"],
    "timestamp": "ISO8601"
}
```

### Step 4: Update Pipeline to Push to WebSocket
- **File**: `main.py`
- **Add**: WebSocket client to push detection data in real-time
- **Implementation**:
  - Import websocket client
  - Push detection JSON every N frames (e.g., every 10 frames to reduce load)
  - Include structured detection data

## Phase 3: Implement Enhanced Telegram Alerts

### Step 5: Create Telegram Alerter with Image Support
- **File**: `pipeline/alert.py`
- **New Class**: `TelegramAlerterWithImage`
- **Features**:
  - Send photo + caption together
  - Include: event type, camera, people count, time, track IDs
- **Message format**:
```
🚨 INTRUSION DETECTED
Camera: cam-1
People: 2
Time: 06:32 AM
Track IDs: 1, 3
```

## Phase 4: Implement Detections JSON API

### Step 6: Add Detections Endpoint
- **File**: `api.py`
- **New Endpoint**: `GET /detections/{camera_id}`
- **Response**:
```json
{
    "camera_id": "cam-0",
    "timestamp": "ISO8601",
    "detections": [
        {"track_id": 1, "type": "person", "confidence": 0.76, "bbox": [x1, y1, x2, y2]},
        {"track_id": 2, "type": "person", "confidence": 0.48, "bbox": [x1, y1, x2, y2]}
    ],
    "stats": {
        "people": 8,
        "vehicles": 2,
        "tracked": 5
    }
}
```

## Phase 5: Update Frontend to Display Live Feed

### Step 7: Update Live View in React
- **File**: `frontend/src/App.js`
- **Modify**: Live view component to use MJPEG stream
- **Use**: `<img src="http://localhost:8000/stream/cam-0" />`

## Implementation Order

1. **api.py** - Add MJPEG stream endpoint + detections endpoint + enhanced WebSocket
2. **pipeline/alert.py** - Add Telegram alerter with image
3. **main.py** - Add WebSocket client to push detections
4. **frontend/src/App.js** - Update live view to show MJPEG stream

## Files to Modify
1. `api.py` - Add MJPEG stream, detections endpoint, enhanced WebSocket manager
2. `pipeline/alert.py` - Add TelegramAlerterWithImage class
3. `main.py` - Add WebSocket client for real-time push
4. `frontend/src/App.js` - Update live view component

## Follow-up Steps
1. Test the MJPEG stream
2. Test WebSocket real-time push
3. Configure Telegram bot with image support
4. Verify live view in dashboard
