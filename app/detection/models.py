# app/detection/models.py

import logging
import os

logger = logging.getLogger(__name__)

# COCO vehicle class IDs
VEHICLE_CLASSES = {2, 3, 5, 7}


class VehicleDetector:
    """
    YOLO-based vehicle detector.
    Lazy-loads model on first inference.
    """

    def __init__(self, model_path="yolov8n.pt", conf=0.4):
        self.model_path = model_path
        self.conf = conf
        self.model = None

    def _load_model(self):
        if self.model is not None:
            return

        from ultralytics import YOLO
        self.model = YOLO(self.model_path)

        logger.info(
            "[VehicleDetector] YOLO loaded (%s exists=%s)",
            self.model_path,
            os.path.exists(self.model_path),
        )

    def detect(self, frame):
        logger.info("[TRACE] VehicleDetector.detect() called")

        self._load_model()

        results = self.model(frame, conf=self.conf, verbose=False)

        detections = []
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                if cls not in VEHICLE_CLASSES:
                    continue

                detections.append({
                    "class": cls,
                    "confidence": float(box.conf[0]),
                    "bbox": box.xyxy[0].tolist(),
                })

        logger.info(
            "[TRACE] VehicleDetector produced %d detections",
            len(detections),
        )

        return detections
