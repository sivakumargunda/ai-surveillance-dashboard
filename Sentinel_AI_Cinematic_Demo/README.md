# Sentinel AI — Cinematic Demo (Standalone)

A standalone, modular cinematic AI surveillance product demo (15–20s) with:
- Scene modules (`scenes/*.js`)
- Cursor glow + neon particles (`animations/*.js`)
- Glassmorphism + cyberpunk aesthetics (`style.css`)
- Smooth transitions (`animations/transitions.js`)
- AI voice narration (Web Speech API) + subtitles (`voice/*.js`)
- Responsive 4K-ready layout (16:9 trailer with letterboxing)

## Run (VS Code Live Server)

1. Open `Sentinel_AI_Cinematic_Demo/` in VS Code.
2. Install the **Live Server** extension (if not already).
3. Right-click `index.html` → **Open with Live Server**.
4. Open in **Chrome**.

## Folder layout
- `index.html` — boot + UI chrome
- `style.css` — cyberpunk + glass UI
- `script.js` — timeline + renderer + wiring
- `assets/` — images/video/music referenced by scenes
- `scenes/` — one file per cinematic section
- `animations/` — transitions, particles, cursor effects, cinematic overlays
- `voice/` — narration + subtitles
- `export/obs-settings.md` — OBS export guidance

## Assets
The demo expects these assets at:
- `assets/logo.png`
- `assets/dashboard-alerts.png`
- `assets/ai-assistant.png`
- `assets/live-detection.png`
- `assets/retail-monitoring.png`
- `assets/bg-music.mp3` (optional)
- `assets/demo-video.mp4` (optional)

If a specific asset is missing, the demo still runs using gradients and the cinematic overlays.

## Controls
- **Replay**: restart the trailer
- **Voice**: toggles narration (SpeechSynthesis)
- **Subtitles**: toggle subtitles

## OBS Export
See `export/obs-settings.md`.

