# app/detection/detector.py

import time
import logging
import threading

from app.config import ROI

logger = logging.getLogger(__name__)


class DetectorWorker(threading.Thread):
    """
    FPS-controlled detection worker.

    Responsibilities:
    - Pull ONLY latest MAIN frame (overwrite-only)
    - Drop frames by design
    - Run detector function (YOLO)
    - Apply ROI filtering
    - Store metadata ONLY (no frames)
    """

    def __init__(
        self,
        cam_id: str,
        camera_manager,
        detection_manager,
        detector_fn,
        fps: int = 3,
    ):
        super().__init__(daemon=True)

        self.cam_id = cam_id
        self.camera_manager = camera_manager
        self.detection_manager = detection_manager
        self.detector_fn = detector_fn

        self.interval = 1.0 / max(fps, 1)
        self.last_run = 0.0
        self.running = True

        # Error backoff
        self.last_error_time = 0.0
        self.error_cooldown = 5.0

    def run(self):
        logger.info(f"[DetectorWorker] Started for camera {self.cam_id}")

        while self.running:
            now = time.time()

            # FPS throttle
            if now - self.last_run < self.interval:
                time.sleep(0.01)
                continue

            self.last_run = now

            try:
                # 🔒 Phase-4 invariant: MAIN frames only
                frame = self.camera_manager.get_main_frame(self.cam_id)

                if frame is None:
                    continue

                # Run detector (YOLO)
                detections = self.detector_fn(frame)

                # Optional ROI filtering
                if ROI:
                    detections = self._filter_by_roi(detections)

                # Store metadata only
                self.detection_manager.update(self.cam_id, detections)

            except Exception as e:
                logger.exception(
                    f"[DetectorWorker] Error for camera {self.cam_id}: {e}"
                )

                # Backoff on repeated failures
                if time.time() - self.last_error_time < self.error_cooldown:
                    time.sleep(self.error_cooldown)

                self.last_error_time = time.time()

    def stop(self):
        self.running = False

    # -------------------------------------------------
    # ROI filtering
    # -------------------------------------------------
    def _filter_by_roi(self, detections):
        """
        detections: list of dicts with 'cx', 'cy' or bbox center
        """
        if not ROI:
            return detections

        x1, y1, x2, y2 = ROI
        filtered = []

        for d in detections:
            cx = d.get("cx")
            cy = d.get("cy")

            if cx is None or cy is None:
                continue

            if x1 <= cx <= x2 and y1 <= cy <= y2:
                filtered.append(d)

        return filtered
