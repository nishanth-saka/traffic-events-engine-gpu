# app/detection/detector.py

import time
import threading
import logging

from app.detection.vehicle_detector import detect_vehicles
from app.ingest.frame.pipeline import process_frame   # ✅ ADDED

logger = logging.getLogger("DetectionWorker")


class DetectionWorker(threading.Thread):
    """
    Stage-1 FPS-controlled detection worker (REAL VEHICLE DETECTION).

    Guarantees:
    - Pulls ONLY latest frame from FrameHub (MAIN stream)
    - Drops frames by design
    - Runs at low, controlled FPS
    - Publishes VEHICLE METADATA ONLY
    - NO plates in metadata (plates handled by Phase-A pipeline)
    """

    def __init__(
        self,
        cam_id: str,
        frame_hub,
        detection_manager,
        fps: int = 2,
    ):
        super().__init__(daemon=True)

        self.cam_id = cam_id
        self.frame_hub = frame_hub
        self.detection_manager = detection_manager

        self.interval = 1.0 / max(fps, 1)
        self.running = True
        self._last_run = 0.0

    def run(self):
        logger.info(
            "[DETECT] Vehicle worker started for %s @ %.1f FPS",
            self.cam_id,
            1.0 / self.interval,
        )

        while self.running:
            now = time.time()
            if now - self._last_run < self.interval:
                time.sleep(0.01)
                continue

            self._last_run = now

            frame = self.frame_hub.get_latest(self.cam_id)
            if frame is None:
                continue

            # -------------------------------------------------
            # Phase-A ANPR pipeline (SIDE-EFFECT ONLY)
            # -------------------------------------------------
            try:
                process_frame(
                    camera_id=self.cam_id,
                    frame_ts=now,
                    frame=frame,
                    frame_store=None,   # not used; safe placeholder
                )
            except Exception:
                logger.exception(
                    "[ANPR] Crash in Phase-A pipeline on %s",
                    self.cam_id,
                )

            try:
                vehicles = detect_vehicles(frame)

                # ---------------------------------------------
                # Publish VEHICLE metadata ONLY
                # ---------------------------------------------
                self.detection_manager.update(
                    self.cam_id,
                    vehicles=vehicles,
                    plates=[],   # 🔒 plates intentionally empty here
                )

                logger.info(
                    "[DETECT] %s heartbeat | vehicles=%d",
                    self.cam_id,
                    len(vehicles),
                )

            except Exception:
                logger.exception(
                    "[DETECT] Crash in vehicle detection on %s",
                    self.cam_id,
                )
