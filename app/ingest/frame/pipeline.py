# app/ingest/frame/pipeline.py

import logging
from typing import List, Dict, Any, Optional

from app.ingest.frame.plate_proposal import propose_plate_regions
from app.ingest.frame.quality_gate import evaluate_plate_quality
from app.ingest.frame.ocr import run_ocr
from app.ingest.frame.events import emit_event

logger = logging.getLogger(__name__)

# ------------------------------------
# Hybrid mode flags
# ------------------------------------
ENABLE_CANDIDATE_ANPR = True

CANDIDATE_CONF_THRESHOLD = 0.30
CONFIRMED_CONF_THRESHOLD = 0.75

# Cheap sanity gate to avoid total junk
MIN_PLATE_W = 60
MIN_PLATE_H = 20


def process_frame(
    *,
    camera_id: str,
    frame_ts: float,
    frame,
    frame_store=None,   # ✅ accepted (router + detector)
    vehicles: Optional[List[Dict[str, Any]]] = None,  # ✅ optional
):
    """
    Phase A — Hybrid ANPR pipeline.

    Responsibilities:
    - Consume vehicle metadata if available
    - Propose plate regions
    - Emit candidate ANPR (fast, noisy)
    - Emit confirmed ANPR (strict, trusted)

    Side-effects only: events + logs
    """

    vehicle_count = len(vehicles) if vehicles else 0
    logger.info(
        "[PIPELINE] start | cam=%s vehicles=%d",
        camera_id,
        vehicle_count,
    )

    # -------------------------------------------------
    # Optional frame store update (safe no-op if None)
    # -------------------------------------------------
    if frame_store is not None:
        try:
            frame_store.update(
                camera_id=camera_id,
                frame=frame,
                ts=frame_ts,
            )
        except Exception:
            logger.exception(
                "[PIPELINE] frame_store update failed | cam=%s",
                camera_id,
            )

    # -------------------------------------------------
    # No vehicles → nothing to process
    # -------------------------------------------------
    if not vehicles:
        emit_event(
            "frame.no_vehicle",
            camera_id=camera_id,
            ts=frame_ts,
        )
        logger.debug(
            "[PIPELINE] skip | cam=%s reason=no_vehicles",
            camera_id,
        )
        return

    # -------------------------------------------------
    # ANPR outcome aggregation
    # -------------------------------------------------
    confirmed_count = 0
    confirmed_conf_sum = 0.0

    # -------------------------------------------------
    # Per-vehicle processing
    # -------------------------------------------------
    for vehicle in vehicles:
        vehicle_crop = vehicle.get("crop")
        if vehicle_crop is None:
            continue

        plate_candidates = propose_plate_regions(vehicle_crop)

        if not plate_candidates:
            emit_event(
                "vehicle.no_plate",
                camera_id=camera_id,
                ts=frame_ts,
            )
            continue

        # -------------------------------------------------
        # Per-plate processing
        # -------------------------------------------------
        for plate in plate_candidates:
            plate_img = plate.get("crop")
            if plate_img is None:
                continue

            h, w = plate_img.shape[:2]

            # -------------------------------------------------
            # Cheap sanity gate
            # -------------------------------------------------
            if h < MIN_PLATE_H or w < MIN_PLATE_W:
                continue

            # =================================================
            # HYBRID PATH 1 — CANDIDATE OCR (FAST / NOISY)
            # =================================================
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

            # =================================================
            # HYBRID PATH 2 — CONFIRMED OCR (STRICT)
            # =================================================
            quality = evaluate_plate_quality(plate_img)

            # ✅ FIX 1 + FIX 2
            if not quality.passed:
                emit_event(
                    "plate.detected_unreadable",
                    camera_id=camera_id,
                    ts=frame_ts,
                    reason=quality.reason,
                    score=quality.score,
                    metrics=quality.metrics,
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
                    metrics=quality.metrics,
                )
                continue

            # ✅ TRUSTED NUMBER PLATE
            emit_event(
                "anpr.confirmed",
                camera_id=camera_id,
                ts=frame_ts,
                text=confirmed_ocr["text"],
                confidence=confirmed_ocr["confidence"],
                metrics=quality.metrics,
            )

            confirmed_count += 1
            confirmed_conf_sum += confirmed_ocr["confidence"]

    # -------------------------------------------------
    # ANPR outcome log
    # -------------------------------------------------
    avg_conf = (
        confirmed_conf_sum / confirmed_count
        if confirmed_count > 0
        else 0.0
    )

    logger.info(
        "[ANPR] completed | cam=%s confirmed=%d avg_conf=%.2f",
        camera_id,
        confirmed_count,
        avg_conf,
    )

    logger.info(
        "[PIPELINE] end | cam=%s",
        camera_id,
    )
