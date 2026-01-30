# app/detection/models.py

import logging

logger = logging.getLogger(__name__)


class VehicleDetector:
    def __init__(self, model_path="yolov8n.pt", conf=0.4):
        self.model_path = model_path
        self.conf = conf
        self.model = None

    def _load_model(self):
        if self.model is not None:
            return

        from ultralytics import YOLO
        self.model = YOLO(self.model_path)
        logger.info("[VehicleDetector] Model loaded")

    def detect(self, frame):
        self._load_model()

        results = self.model(frame, conf=self.conf, verbose=False)

        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({
                    "class": int(box.cls[0]),
                    "confidence": float(box.conf[0]),
                    "bbox": box.xyxy[0].tolist(),
                })

        return detections
