# app/detection/detection_manager.py

import time
import threading
import logging

logger = logging.getLogger(__name__)


class DetectionManager:
    """
    Thread-safe detection cache.
    Stores latest detections per camera.
    """

    def __init__(self):
        # cam_id -> { ts, boxes, latency_ms }
        self._latest = {}
        self._lock = threading.Lock()

    def update(self, cam_id: str, detections: list, latency_ms: float):
        with self._lock:
            self._latest[cam_id] = {
                "ts": time.time(),
                "boxes": detections,
                "latency_ms": latency_ms,
            }

        logger.info(
            "[TRACE][%s] DetectionManager.update(): %d boxes (%.1f ms)",
            cam_id,
            len(detections),
            latency_ms,
        )

    def get(self, cam_id: str, max_age_sec: float = 1.0):
        with self._lock:
            data = self._latest.get(cam_id)

        if not data:
            return []

        if time.time() - data["ts"] > max_age_sec:
            return []

        return data["boxes"]
