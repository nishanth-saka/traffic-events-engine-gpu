# app/ingest/frame/pipeline.py

import logging

from app.ingest.frame.vehicle import detect_vehicles
from app.ingest.frame.plate_proposal import propose_plate_regions
from app.ingest.frame.quality_gate import evaluate_plate_quality
from app.ingest.frame.ocr import run_ocr
from app.ingest.frame.events import emit_event
from app.state import app_state

logger = logging.getLogger(__name__)


def process_frame(
    *,
    camera_id: str,
    frame_ts: float,
    frame,
):
    """
    Stage-2 frame processing pipeline.

    - Receives MAIN frame (already ingested)
    - Does NOT own storage
    - Emits detections + events
    """

    logger.debug(
        "[PIPELINE] process_frame | camera_id=%s ts=%s",
        camera_id,
        frame_ts,
    )

    # -------------------------------------------------
    # Vehicle detection
    # -------------------------------------------------
    vehicles = detect_vehicles(frame)

    # 🔑 Publish detections for preview / temporal layers
    app_state.detection_manager.update(
        cam_id=camera_id,
        detections=vehicles,
    )

    if not vehicles:
        emit_event(
            "frame.dropped.no_vehicle",
            camera_id=camera_id,
            ts=frame_ts,
        )
        return

    for vehicle in vehicles:
        x1, y1, x2, y2 = vehicle["bbox"]
        vehicle_crop = frame[y1:y2, x1:x2]

        # -----------------------------
        # Plate proposal
        # -----------------------------
        plate_candidates = propose_plate_regions(vehicle_crop)

        if not plate_candidates:
            emit_event(
                "vehicle.no_plate_candidate",
                camera_id=camera_id,
                vehicle=vehicle,
            )
            continue

        for plate in plate_candidates:
            plate_crop = plate["crop"]

            # -----------------------------
            # Quality gate
            # -----------------------------
            gate = evaluate_plate_quality(plate_crop)

            if not gate.passed:
                emit_event(
                    "plate.rejected",
                    camera_id=camera_id,
                    reason=gate.reason,
                    score=gate.score,
                )
                continue

            # -----------------------------
            # OCR
            # -----------------------------
            ocr = run_ocr(plate_crop)

            if ocr["confidence"] < 0.6:
                emit_event(
                    "ocr.low_confidence",
                    camera_id=camera_id,
                    plate=ocr,
                )
                continue

            emit_event(
                "plate.ocr.success",
                camera_id=camera_id,
                plate=ocr,
                vehicle=vehicle,
            )
