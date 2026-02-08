# app/detection/detection_manager.py

import threading
import time
from typing import Dict, List


class DetectionManager:
    """
    Thread-safe detection metadata cache.

    Stores ONLY metadata (no frames):
    - vehicles
    - plates
    - timestamps
    """

    def __init__(self):
        # cam_id -> data
        self._data: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def update(
        self,
        cam_id: str,
        *,
        vehicles: List[dict],
        plates: List[dict],
    ):
        with self._lock:
            self._data[cam_id] = {
                "ts": time.time(),
                "vehicles": vehicles,
                "plates": plates,
            }

    def get(self, cam_id: str, max_age_sec: float = 1.0) -> dict | None:
        with self._lock:
            entry = self._data.get(cam_id)
            if not entry:
                return None

            if time.time() - entry["ts"] > max_age_sec:
                return None

            return entry
