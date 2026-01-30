import logging
from ultralytics import YOLO

logger = logging.getLogger(__name__)

_model = YOLO("yolov8n.pt")  # loads once at import

VEHICLE_CLASSES = {2, 3, 5, 7}  # car, motorcycle, bus, truck

def detect_vehicles(frame):
    results = _model(frame, verbose=False)

    vehicles = []
    h, w = frame.shape[:2]

    for r in results:
        for box in r.boxes:
            cls = int(box.cls)
            if cls not in VEHICLE_CLASSES:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            crop = frame[y1:y2, x1:x2]

            vehicles.append({
                "bbox": [x1, y1, x2, y2],
                "class": cls,
                "confidence": float(box.conf),
                "crop": crop,
            })

    logger.info("[VEHICLE] detected %d vehicles", len(vehicles))
    return vehicles
