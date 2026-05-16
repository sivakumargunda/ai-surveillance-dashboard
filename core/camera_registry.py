from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import CAMERA_REGISTRY_PATH, MULTI_CAM_URLS


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_artifacts_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


class CameraRegistry:
    """Manage cameras stored in a JSON registry.

    Storage: artifacts/cameras.json (configurable)
    """

    def __init__(self, registry_path: str = CAMERA_REGISTRY_PATH) -> None:
        self.registry_path = registry_path

    def _default_camera(self, cam_id: str, url: str, name: str) -> Dict[str, Any]:
        return {
            "id": cam_id,
            "name": name,
            "url": url,
            "enabled": True,
            "rotate": 0,
            "conf": 0.40,
            "zones": [],
            "added_at": _utc_now_iso(),
            "status": "online",
        }

    def _load_raw(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.registry_path):
            # First startup migration
            _ensure_artifacts_dir(self.registry_path)
            urls = [u.strip() for u in (MULTI_CAM_URLS or []) if u and u.strip()]
            cameras: List[Dict[str, Any]] = []
            for i, url in enumerate(urls, start=1):
                cam_id = f"cam-mobile-{i}"
                cameras.append(self._default_camera(cam_id=cam_id, url=url, name=f"Camera {i}"))
            self.save(cameras)
            return cameras

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
        except Exception:
            return []

    def load(self) -> List[Dict[str, Any]]:
        """Load cameras from JSON."""
        return self._load_raw()

    def save(self, cameras: List[Dict[str, Any]]) -> None:
        """Write cameras to JSON."""
        _ensure_artifacts_dir(self.registry_path)
        tmp_path = self.registry_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(cameras, f, indent=2)
        os.replace(tmp_path, self.registry_path)

    def _next_id(self, cameras: List[Dict[str, Any]]) -> str:
        # Prefer cam-mobile-N sequence. If absent, assign next max+1.
        max_n = 0
        for c in cameras:
            cam_id = str(c.get("id", ""))
            if cam_id.startswith("cam-mobile-"):
                try:
                    n = int(cam_id.split("cam-mobile-", 1)[1])
                    max_n = max(max_n, n)
                except ValueError:
                    continue
        return f"cam-mobile-{max_n + 1}"

    def add(self, url: str, name: str) -> Dict[str, Any]:
        cameras = self.load()
        cam_id = self._next_id(cameras)
        cam = self._default_camera(cam_id=cam_id, url=url, name=name)
        cameras.append(cam)
        self.save(cameras)
        return cam

    def remove(self, cam_id: str) -> bool:
        cameras = self.load()
        new_cameras = [c for c in cameras if str(c.get("id")) != str(cam_id)]
        if len(new_cameras) == len(cameras):
            return False
        self.save(new_cameras)
        return True

    def update(self, cam_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        cameras = self.load()
        updated: Optional[Dict[str, Any]] = None
        for c in cameras:
            if str(c.get("id")) == str(cam_id):
                for k, v in fields.items():
                    if k == "id":
                        continue
                    c[k] = v
                updated = c
                break
        if updated is None:
            return None
        self.save(cameras)
        return updated

    def get(self, cam_id: str) -> Optional[Dict[str, Any]]:
        cameras = self.load()
        for c in cameras:
            if str(c.get("id")) == str(cam_id):
                return c
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        return self.load()

