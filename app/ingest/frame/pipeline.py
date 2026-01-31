# app/ingest/frame/pipeline.py

import logging

# Re-enable ML imports and logic
from app.ingest.frame.vehicle import detect_vehicles
from app.ingest.frame.plate_proposal import propose_plate_regions
from app.ingest.frame.quality_gate import evaluate_plate_quality
from app.ingest.frame.ocr import run_ocr
from app.ingest.frame.events import emit_event

logger = logging.getLogger(__name__)


def process_frame(*, camera_id: str, frame_ts: float, frame, frame_store):
    from app.state import app_state  # Lazy import to resolve circular dependency

    vehicles = detect_vehicles(frame)

    app_state.detection_manager.update(
        cam_id=camera_id,
        detections=vehicles,
    )

    # Placeholder logic for testing
    logger.info("Processing frame for camera_id: %s", camera_id)
