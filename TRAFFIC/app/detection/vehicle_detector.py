# app/detection/vehicle_detector.py
import logging
from ultralytics import YOLO

logger = logging.getLogger("VehicleDetector")

# Load once at import (important for performance)
_MODEL = YOLO("yolov8n.pt")

# COCO vehicle classes
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


def detect_vehicles(frame):
    """
    Run YOLO vehicle detection on a frame.

    Returns:
        List[dict]:
            {
                "bbox": (x1, y1, x2, y2),
                "confidence": float,
                "class": str
            }
    """
    results = _MODEL(frame, verbose=False)

    h, w = frame.shape[:2]
    vehicles = []

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls)
            if cls_id not in VEHICLE_CLASSES:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Clamp bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

            vehicles.append({
                "bbox": (x1, y1, x2, y2),
                "confidence": float(box.conf),
                "class": VEHICLE_CLASSES[cls_id],
            })

    logger.debug("Detected %d vehicles", len(vehicles))
    return vehicles
