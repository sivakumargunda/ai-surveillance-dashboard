"""
pipeline/alert.py
Console-based alert handler with cooldowns and database storage.
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from datetime import datetime
from typing import Optional

from core.config import ENABLE_ALERT_BEEP
from core.models import Alert, SessionLocal
from pipeline.activity import ActivityEvent, ActivityType, EventState

COOLDOWN: dict[ActivityType, float] = {
    ActivityType.CROWD: 5.0,
    ActivityType.ZONE_INTRUSION: 10.0,
}

COLOURS: dict[ActivityType, str] = {
    ActivityType.CROWD: "\033[94m",
    ActivityType.ZONE_INTRUSION: "\033[95m",
}

CRITICAL_ALERTS = {
    ActivityType.ZONE_INTRUSION,
}

ALERT_MESSAGES: dict[ActivityType, str] = {
    ActivityType.CROWD: "Crowd gathering detected",
    ActivityType.ZONE_INTRUSION: "Restricted zone intrusion detected",
}

RESET = "\033[0m"
BOLD = "\033[1m"


def _beep() -> None:
    try:
        import winsound

        winsound.Beep(1200, 250)
    except Exception:
        print("\a", end="", flush=True)


class ConsoleAlerter:
    """
    Prints activity events to the console with rate-limiting.
    """

    def __init__(self) -> None:
        self._last_alert: dict[tuple[str, ActivityType], float] = defaultdict(float)

    def handle(self, event: ActivityEvent) -> bool:
        if event.state not in (EventState.START, EventState.END):
            return False  # Only alert on START/END
        
        key = (event.camera_id, event.activity_type, event.state.value)
        now = time.time()
        cooldown = COOLDOWN.get(event.activity_type, 5.0)

        if now - self._last_alert[key] < cooldown:
            return False

        self._last_alert[key] = now
        colour = COLOURS.get(event.activity_type, "")
        ts = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
        message = f"{event.state.value.upper()} - {ALERT_MESSAGES.get(event.activity_type, 'Activity detected')}"
        critical = "  critical=yes" if event.activity_type in CRITICAL_ALERTS else ""

        if ENABLE_ALERT_BEEP:
            _beep()

        print(
            f"{colour}{BOLD}[ALERT {ts}] {event.activity_type.upper()} {event.state.value.upper()}{RESET}{colour}"
            f"  id={event.event_id[:8]}"
            f"  message=\"{message}\""
            f"  camera={event.camera_id}"
            f"  tracks={event.track_ids}"
            + (f"  {' '.join(f'{k}={v}' for k, v in event.extra.items())}" if event.extra else "")
            + critical
            + RESET
        )
        return True

    def handle_all(self, events: list[ActivityEvent]) -> list[ActivityEvent]:
        emitted: list[ActivityEvent] = []
        for event in events:
            if self.handle(event):
                emitted.append(event)
        return emitted


class DatabaseAlerter:
    """
    Saves activity events to the database.
    """

    def __init__(self) -> None:
        pass

    def handle(self, event: ActivityEvent, snapshot_path: Optional[str] = None) -> bool:
        """Save alert to database."""
        if event.state not in (EventState.START, EventState.END):
            return False  # Only save START/END

        try:
            db = SessionLocal()
            db_alert = Alert(
                event_id=event.event_id,
                activity_type=event.activity_type,
                event_state=event.state.value,
                track_ids=json.dumps(event.track_ids),
                camera_id=event.camera_id,
                timestamp=datetime.fromtimestamp(event.timestamp),
                message=f"{event.state.value.upper()} - {ALERT_MESSAGES.get(event.activity_type, 'Activity detected')}",
                extra_data=json.dumps(event.extra) if event.extra else None,
                snapshot_path=snapshot_path
            )
            db.add(db_alert)
            db.commit()
            db.close()
            return True
        except Exception as e:
            print(f"[DatabaseAlerter] Error saving alert: {e}")
            return False

    def handle_all(self, events: list[ActivityEvent], snapshot_paths: Optional[list[str]] = None) -> list[ActivityEvent]:
        """Save all events to database."""
        if snapshot_paths is None:
            snapshot_paths = [None] * len(events)

        emitted: list[ActivityEvent] = []
        for event, snapshot_path in zip(events, snapshot_paths):
            if self.handle(event, snapshot_path):
                emitted.append(event)
        return emitted


class TelegramAlerterWithImage:
    """
    Sends Telegram alerts with image + detailed message.
    
    Requires environment variables:
    - TELEGRAM_BOT_TOKEN: Your bot token from @BotFather
    - TELEGRAM_CHAT_ID: Your chat ID
    """

    def __init__(self) -> None:
        self._token = os.getenv("TELEGRAM_BOT_TOKEN")
        self._chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self._last_alert: dict[tuple[str, ActivityType], float] = defaultdict(float)
        
    def _send_photo(self, photo_path: str, caption: str) -> bool:
        """Send photo with caption to Telegram."""
        if not self._token or not self._chat_id:
            print("[TelegramAlerter] Bot token or chat ID not configured")
            return False
            
        import urllib.request
        import urllib.parse
        
        url = f"https://api.telegram.org/bot{self._token}/sendPhoto"
        
        # Read and encode the image
        try:
            with open(photo_path, 'rb') as f:
                photo_data = f.read()
        except Exception as e:
            print(f"[TelegramAlerter] Error reading image: {e}")
            return False
        
        # Create multipart form data
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = f'--{boundary}\r\n'.encode()
        body += f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'.encode()
        body += f'{self._chat_id}\r\n'.encode()
        body += f'--{boundary}\r\n'.encode()
        body += f'Content-Disposition: form-data; name="photo"; filename="{os.path.basename(photo_path)}"\r\n'.encode()
        body += b'Content-Type: image/jpeg\r\n\r\n'
        body += photo_data
        body += b'\r\n'
        body += f'--{boundary}\r\n'.encode()
        body += f'Content-Disposition: form-data; name="caption"\r\n\r\n'.encode()
        body += caption.encode()
        body += f'\r\n--{boundary}--\r\n'.encode()
        
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(request, timeout=10):
                return True
        except Exception as e:
            print(f"[TelegramAlerter] Error sending photo: {e}")
            return False
    
    def _send_message(self, text: str) -> bool:
        """Send text message to Telegram."""
        if not self._token or not self._chat_id:
            return False
            
        import urllib.request
        import urllib.parse
        
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML"
        }).encode()
        
        request = urllib.request.Request(url, data=data, method="POST")
        
        try:
            with urllib.request.urlopen(request, timeout=10):
                return True
        except Exception as e:
            print(f"[TelegramAlerter] Error sending message: {e}")
            return False

    def handle(self, event: ActivityEvent, snapshot_path: Optional[str] = None) -> bool:
        """Send alert with image to Telegram."""
        if event.state != EventState.START:
            return False  # Only send on START
            
        key = (event.camera_id, event.activity_type)
        now = time.time()
        cooldown = COOLDOWN.get(event.activity_type, 30.0)
        
        if now - self._last_alert[key] < cooldown:
            return False
            
        self._last_alert[key] = now
        
# Format message
        activity_emojis = {
            ActivityType.CROWD: "👥",
            ActivityType.ZONE_INTRUSION: "🚨",
        }
        emoji = activity_emojis.get(event.activity_type, "⚠️")
        
        timestamp_str = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
        message = f"""{emoji} <b>{event.activity_type.upper().replace('_', ' ')} DETECTED</b>

<b>Camera:</b> {event.camera_id}
<b>Time:</b> {timestamp_str}
<b>Track IDs:</b> {', '.join(str(t) for t in event.track_ids) if event.track_ids else 'N/A'}
<b>Count:</b> {event.extra.get('count', len(event.track_ids))}"""
        
        # Send message first
        self._send_message(message)
        
        # Send photo if available
        if snapshot_path and os.path.exists(snapshot_path):
            photo_caption = f"{emoji} Event snapshot - {event.activity_type}"
            self._send_photo(snapshot_path, photo_caption)
            
        return True

    def handle_all(self, events: list[ActivityEvent], snapshot_paths: Optional[list[str]] = None) -> list[ActivityEvent]:
        """Send all events to Telegram."""
        if snapshot_paths is None:
            snapshot_paths = [None] * len(events)
            
        emitted: list[ActivityEvent] = []
        for event, snapshot_path in zip(events, snapshot_paths):
            if self.handle(event, snapshot_path):
                emitted.append(event)
        return emitted
