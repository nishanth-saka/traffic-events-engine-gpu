# app/detection/detection_manager.py

import threading
import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class DetectionManager:
    """
    Thread-safe detection store + accuracy logger.

    Stores metadata only (no frames).
    Periodically logs detection statistics per camera.
    """

    def __init__(self, log_interval_sec: float = 10.0):
        self._latest = {}
        self._lock = threading.Lock()

        # 🔍 Accuracy stats
        self._stats = defaultdict(lambda: {
            "total": 0,
            "empty": 0,
            "classes": defaultdict(list),  # class -> [confidences]
            "latencies": [],
            "last_log": 0.0,
        })

        self.log_interval_sec = log_interval_sec

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------
    def update(self, cam_id: str, detections: list, latency_ms: float):
        """
        detections: list of dicts:
          {
            "class": str,
            "confidence": float,
            "bbox": [x1, y1, x2, y2]
          }
        """
        now = time.time()

        with self._lock:
            self._latest[cam_id] = {
                "ts": now,
                "boxes": detections,
            }

            stats = self._stats[cam_id]
            stats["total"] += 1
            stats["latencies"].append(latency_ms)

            if not detections:
                stats["empty"] += 1
            else:
                for d in detections:
                    stats["classes"][d["class"]].append(d["confidence"])

            # Periodic accuracy log
            if now - stats["last_log"] >= self.log_interval_sec:
                self._log_stats(cam_id, stats)
                stats["last_log"] = now

    def get(self, cam_id: str, max_age_sec: float = 1.0):
        """
        Returns latest detections or [] if stale / missing.
        """
        with self._lock:
            data = self._latest.get(cam_id)
            if not data:
                return []

            if time.time() - data["ts"] > max_age_sec:
                return []

            return data["boxes"]

    # -------------------------------------------------
    # Internal
    # -------------------------------------------------
    def _log_stats(self, cam_id: str, stats: dict):
        total = stats["total"]
        empty = stats["empty"]
        latencies = stats["latencies"]

        avg_latency = (
            sum(latencies) / len(latencies)
            if latencies else 0.0
        )

        logger.info(
            "[DETECTION][%s] total=%d empty=%d avg_latency=%.1fms",
            cam_id,
            total,
            empty,
            avg_latency,
        )

        for cls, confs in stats["classes"].items():
            avg_conf = sum(confs) / len(confs) if confs else 0.0
            logger.info(
                "[DETECTION][%s]   %s: %d (avg_conf=%.2f)",
                cam_id,
                cls,
                len(confs),
                avg_conf,
            )

        # Reset rolling stats (important!)
        stats["total"] = 0
        stats["empty"] = 0
        stats["classes"].clear()
        stats["latencies"].clear()
