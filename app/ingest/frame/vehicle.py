# app/detection/vehicle_detector.py

import logging
from ultralytics import YOLO

logger = logging.getLogger(__name__)

# Load once at import (correct)
_model = YOLO("yolov8n.pt")

# COCO vehicle class mapping
VEHICLE_CLASS_MAP = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


def detect_vehicles(frame, roi=None):
    """
    Headless vehicle detector.

    Returns list of dicts:
      {
        "class": str,
        "confidence": float,
        "bbox": [x1, y1, x2, y2]
      }
    """

    results = _model(frame, verbose=False)

    vehicles = []
    h, w = frame.shape[:2]

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls)

            if cls_id not in VEHICLE_CLASS_MAP:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            vehicles.append({
                "bbox": [x1, y1, x2, y2],
                "class": VEHICLE_CLASS_MAP[cls_id],  # ✅ semantic label
                "confidence": float(box.conf),
            })

    logger.info(
        "[VEHICLE] detected %d vehicles (%s)",
        len(vehicles),
        ", ".join(v["class"] for v in vehicles) or "none",
    )

    return vehicles
