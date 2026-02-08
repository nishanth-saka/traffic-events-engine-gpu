# app/frames/snapshot.py

import threading
from typing import Any, Dict


class SnapshotFrameStore:
    """
    Overwrite-only, in-memory frame store.

    - Stores latest frame per camera
    - Thread-safe
    - Designed for real-time detection (frame dropping by design)
    """

    def __init__(self):
        self._frames: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def update_frame(self, camera_id: str, frame: Any):
        with self._lock:
            self._frames[camera_id] = frame

    def get_latest_frame(self, camera_id: str):
        with self._lock:
            return self._frames.get(camera_id)

    def camera_ids(self):
        with self._lock:
            return list(self._frames.keys())
