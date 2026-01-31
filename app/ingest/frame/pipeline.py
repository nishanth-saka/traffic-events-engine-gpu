# app/ingest/frame/pipeline.py

import logging
from app.ingest.frame.vehicle import detect_vehicles
from app.ingest.frame.plate_proposal import propose_plate_regions
from app.ingest.frame.quality_gate import evaluate_plate_quality
from app.ingest.frame.ocr import run_ocr
from app.ingest.frame.events import emit_event
from app.state import app_state

logger = logging.getLogger(__name__)


def process_frame(*, camera_id: str, frame_ts: float, frame):
    vehicles = detect_vehicles(frame)

    app_state.detection_manager.update(
        cam_id=camera_id,
        detections=vehicles,
    )

    if not vehicles:
        emit_event("frame.no_vehicle", camera_id=camera_id)
        return

    for vehicle in vehicles:
        x1, y1, x2, y2 = vehicle["bbox"]
        crop = frame[y1:y2, x1:x2]

        plates = propose_plate_regions(crop)
        for plate in plates:
            gate = evaluate_plate_quality(plate["crop"])
            if not gate.passed:
                continue

            ocr = run_ocr(plate["crop"])
            if ocr["confidence"] < 0.6:
                continue

            emit_event(
                "plate.ocr.success",
                camera_id=camera_id,
                plate=ocr,
                vehicle=vehicle,
            )
