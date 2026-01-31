# app/detection/detector.py

import time
import threading
import logging
import numpy as np

logger = logging.getLogger("DetectionWorker")


class DetectionWorker(threading.Thread):
    """
    Minimal FPS-controlled detection worker (NO ML).

    Guarantees:
    - Pulls ONLY latest frame from FrameHub (MAIN stream)
    - Drops frames by design
    - Runs at low, controlled FPS
    - Proves MAIN → detection pipeline is alive
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
            "[DETECT] Minimal worker started for %s @ %.1f FPS",
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

            try:
                h, w = frame.shape[:2]

                # -------------------------------------------------
                # Fake plate proposal (center-lower crop)
                # -------------------------------------------------
                x1 = int(0.30 * w)
                x2 = int(0.70 * w)
                y1 = int(0.55 * h)
                y2 = int(0.75 * h)

                plate_crop = frame[y1:y2, x1:x2]

                plates = [{
                    "bbox": (x1, y1, x2, y2),
                    "conf": 1.0,
                    "source": "fake",
                }]

                vehicles = []  # intentionally empty in Step 1

                # -------------------------------------------------
                # Update detection manager (metadata only)
                # -------------------------------------------------
                self.detection_manager.update(
                    self.cam_id,
                    vehicles=vehicles,
                    plates=plates,
                )

                logger.info(
                    "[DETECT] %s heartbeat | fake_plate=%dx%d",
                    self.cam_id,
                    plate_crop.shape[1],
                    plate_crop.shape[0],
                )

            except Exception:
                logger.exception(
                    "[DETECT] Crash in minimal worker on %s",
                    self.cam_id,
                )
