# OBS export settings (4K-ready)

Goal: export a cinematic 4K trailer (16:9) that matches the demo’s letterboxed stage.

## Recommended canvas
- **Resolution**: 3840x2160 (4K UHD)
- **FPS**: 60 (or 30 if you need smaller file sizes)
- **Color format**: NV12 (typical default)
- **Color space**: Rec.709

## Encoder settings (pick one)

### Option A: x264 (compatibility-first)
- Encoder: **Software (x264)
- Rate Control: **CBR** (or **Quality** if you prefer)
- Bitrate: **60,000–100,000 kbps**
- Keyframe interval: **2** seconds
- Profile: **High**

### Option B: H.264 (hardware, if available)
- Encoder: **Hardware (NVENC / QuickSync)
- Rate Control: **CBR**
- Bitrate: **45,000–80,000 kbps**
- Keyframe interval: **2** seconds

### Option C: H.265 (smaller files)
- Encoder: **Hardware (NVENC)
- Rate Control: **CBR**
- Bitrate: **30,000–70,000 kbps**
- Keyframe interval: **2** seconds

## Scene sources
- Add your browser source:
  - Source type: **Browser**
  - URL: `http://localhost:5500/Sentinel_AI_Cinematic_Demo/index.html` (or Live Server URL)
  - **Capture Method**: “Capture any fullscreen application” (if needed)

## Tips for best results
- Use **Chrome**.
- Disable browser zoom and extensions that may inject UI.
- If autoplay voice is blocked, click the page once before starting the recording.
- Record at the same FPS you plan to export.

