# app/ingest/frame/pipeline.py

import logging

from app.ingest.frame.vehicle import detect_vehicles
from app.ingest.frame.plate_proposal import propose_plate_regions
from app.ingest.frame.quality_gate import evaluate_plate_quality
from app.ingest.frame.ocr import run_ocr
from app.ingest.frame.events import emit_event
from app.shared import app_state

logger = logging.getLogger(__name__)

# ------------------------------------
# Hybrid mode flags
# ------------------------------------
ENABLE_CANDIDATE_ANPR = True
CANDIDATE_CONF_THRESHOLD = 0.30
CONFIRMED_CONF_THRESHOLD = 0.75


def process_frame(
    *,
    camera_id: str,
    frame_ts: float,
    frame,
    frame_store,
):
    """
    Hybrid Phase A pipeline.

    - Candidate ANPR: fast, noisy, visible
    - Confirmed ANPR: gated, trusted
    """

    # -----------------------------
    # Vehicle detection
    # -----------------------------
    vehicles = detect_vehicles(frame)

    # Update detection manager (used by preview / overlays)
    app_state.detection_manager.update(
        cam_id=camera_id,
        detections=vehicles,
    )

    if not vehicles:
        emit_event(
            "frame.no_vehicle",
            camera_id=camera_id,
            ts=frame_ts,
        )
        return

    # -----------------------------
    # Per-vehicle processing
    # -----------------------------
    for vehicle in vehicles:
        vehicle_crop = vehicle.get("crop")

        if vehicle_crop is None:
            continue

        plate_candidates = propose_plate_regions(vehicle_crop)
        logger.warning(
            "[DEBUG] cam=%s plate_candidates=%d",
            camera_id,
            len(plate_candidates),
        )
        
        for plate in plate_candidates:
            logger.warning(
                "[DEBUG] plate keys = %s",
                list(plate.keys()),
            )

        if not plate_candidates:
            emit_event(
                "vehicle.no_plate",
                camera_id=camera_id,
                ts=frame_ts,
            )
            continue

        # -----------------------------
        # Per-plate processing
        # -----------------------------
        for plate in plate_candidates:
            plate_img = plate.get("crop")

            if plate_img is None:
                continue

            # =====================================================
            # HYBRID PATH 1: CANDIDATE OCR (UNGATED, FOR VISIBILITY)
            # =====================================================
            if ENABLE_CANDIDATE_ANPR:
                candidate_ocr = run_ocr(plate_img)

                if (
                    candidate_ocr.get("text")
                    and candidate_ocr.get("confidence", 0.0)
                    >= CANDIDATE_CONF_THRESHOLD
                ):
                    emit_event(
                        "anpr.candidate",
                        camera_id=camera_id,
                        ts=frame_ts,
                        text=candidate_ocr["text"],
                        confidence=candidate_ocr["confidence"],
                    )

            # =====================================================
            # HYBRID PATH 2: CONFIRMED OCR (STRICT, TRUSTED)
            # =====================================================
            quality = evaluate_plate_quality(plate_img)

            if not quality["allowed"]:
                emit_event(
                    "plate.detected_unreadable",
                    camera_id=camera_id,
                    ts=frame_ts,
                    reason=quality["reason"],
                    metrics=quality["metrics"],
                )
                continue

            confirmed_ocr = run_ocr(plate_img)

            if (
                not confirmed_ocr.get("text")
                or confirmed_ocr.get("confidence", 0.0)
                < CONFIRMED_CONF_THRESHOLD
            ):
                emit_event(
                    "anpr.rejected",
                    camera_id=camera_id,
                    ts=frame_ts,
                    reason="low_confidence",
                    confidence=confirmed_ocr.get("confidence", 0.0),
                    metrics=quality["metrics"],
                )
                continue

            # ✅ THIS IS THE REAL NUMBER PLATE LOG
            emit_event(
                "anpr.confirmed",
                camera_id=camera_id,
                ts=frame_ts,
                text=confirmed_ocr["text"],
                confidence=confirmed_ocr["confidence"],
                metrics=quality["metrics"],
            )

    logger.info(
        "[PIPELINE] frame processed | cam=%s vehicles=%d",
        camera_id,
        len(vehicles),
    )
