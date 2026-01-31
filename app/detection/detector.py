# app/detection/detection_worker.py

import time
import threading
import logging
import numpy as np

logger = logging.getLogger("DetectionWorker")


class DetectionWorker(threading.Thread):
    """
    FPS-controlled detection worker.

    - Pulls ONLY latest frame from FrameHub
    - Drops frames by design
    - Runs YOLO at low FPS (3–5)
    - Pushes metadata ONLY
    """

    def __init__(
        self,
        cam_id: str,
        frame_hub,
        detection_manager,
        model,
        fps: int = 3,
        conf: float = 0.4,
    ):
        super().__init__(daemon=True)
        self.cam_id = cam_id
        self.frame_hub = frame_hub
        self.detection_manager = detection_manager
        self.model = model
        self.conf = conf

        self.interval = 1.0 / max(fps, 1)
        self.running = True
        self._last_run = 0.0

    def run(self):
        logger.info(
            "[DETECT] Worker started for %s @ %.1f FPS",
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
                results = self.model(
                    frame,
                    conf=self.conf,
                    verbose=False,
                )

                vehicles = []
                plates = []

                for r in results:
                    if r.boxes is None:
                        continue

                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])

                        x1, y1, x2, y2 = map(
                            int, box.xyxy[0].tolist()
                        )

                        entry = {
                            "bbox": (x1, y1, x2, y2),
                            "conf": conf,
                            "cls": cls_id,
                        }

                        # ---- COCO vehicle classes ----
                        if cls_id in {2, 3, 5, 7}:  # car, moto, bus, truck
                            vehicles.append(entry)

                        # ---- License plate class (depends on model) ----
                        if cls_id == 0:  # plate class (common)
                            plates.append(entry)

                self.detection_manager.update(
                    self.cam_id,
                    vehicles=vehicles,
                    plates=plates,
                )

                if plates:
                    logger.info(
                        "[DETECT] %s plates=%d vehicles=%d",
                        self.cam_id,
                        len(plates),
                        len(vehicles),
                    )

            except Exception:
                logger.exception("[DETECT] Crash on %s", self.cam_id)
