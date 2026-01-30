# app/detection/detector.py

import time
import logging
import threading

logger = logging.getLogger(__name__)


class DetectorWorker(threading.Thread):
    """
    Headless detection worker.

    - Pulls latest frame
    - Runs detector
    - Stores normalized detections
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

        self.last_error_time = 0.0
        self.error_backoff_sec = 5.0

    def run(self):
        logger.info("[DetectorWorker] Started for %s", self.cam_id)

        while self.running:
            now = time.time()

            if now - self.last_run < self.interval:
                time.sleep(0.005)
                continue

            self.last_run = now

            try:
                frame = self.camera_manager.get_latest_frame(self.cam_id)
                if frame is None:
                    continue

                logger.info(
                    "[TRACE][%s] Frame received shape=%s",
                    self.cam_id,
                    getattr(frame, "shape", None),
                )

                start = time.time()
                detections = self.detector_fn(frame)
                latency_ms = (time.time() - start) * 1000.0

                logger.info(
                    "[TRACE][%s] Detector produced %d detections (%.1f ms)",
                    self.cam_id,
                    len(detections),
                    latency_ms,
                )

                normalized = []
                for d in detections:
                    normalized.append({
                        "class": d["class"],
                        "confidence": float(d["confidence"]),
                        "bbox": d["bbox"],
                    })

                self.detection_manager.update(
                    self.cam_id,
                    normalized,
                    latency_ms=latency_ms,
                )

            except Exception:
                if time.time() - self.last_error_time > self.error_backoff_sec:
                    logger.exception(
                        "[DetectorWorker][%s] detection error",
                        self.cam_id,
                    )
                    self.last_error_time = time.time()
