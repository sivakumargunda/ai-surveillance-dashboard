# Zone Intrusion Clips Feature

## Plan Steps:
- [ ] 1. Backend: Track zone_intrusion event_id in ActivityAnalyzer (already active_events dict).
- [ ] 2. Modify main.py: When zone_intrusion START → start cv2.VideoWriter for clip.
- [ ] 3. On matching END → stop writer, save MP4 to artifacts/clips/{event_id}.mp4, add clip_path to Alert extra_data.
- [ ] 4. Update api.py: Serve /clips/{filename}, add clips section endpoint.
- [ ] 5. Frontend App.js: New 'Zone Intrusion Clips' section with video players.
- [ ] 6. Config: CLIP_FPS=10, CLIP_CODEC='mp4v'.
- [ ] 7. Test with `python run_all.py` or `main.py`.

Current: Planning complete.
