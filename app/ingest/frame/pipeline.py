# app/ingest/frame/pipeline.py

import logging
from typing import List, Dict, Any

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
    vehicles: List[Dict[str, Any]],
):
    """
    Phase A — Hybrid ANPR pipeline.

    Responsibilities:
    - Consume vehicle metadata (NO vehicle detection here)
    - Propose plate regions
    - Emit candidate ANPR (fast, noisy)
    - Emit confirmed ANPR (strict, trusted)

    Side-effects only: events + logs
    """

    logger.info("[PIPELINE] start | cam=%s vehicles=%d", camera_id, len(vehicles))

    if not vehicles:
        emit_event(
            "frame.no_vehicle",
            camera_id=camera_id,
            ts=frame_ts,
        )
        return

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
            # Cheap sanity gate (prevents total garbage OCR)
            # -------------------------------------------------
            if h < MIN_PLATE_H or w < MIN_PLATE_W:
                continue

            # =================================================
            # HYBRID PATH 1 — CANDIDATE OCR (UNGATED)
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

            # ✅ TRUSTED, REAL NUMBER PLATE
            emit_event(
                "anpr.confirmed",
                camera_id=camera_id,
                ts=frame_ts,
                text=confirmed_ocr["text"],
                confidence=confirmed_ocr["confidence"],
                metrics=quality["metrics"],
            )

    logger.info("[PIPELINE] end | cam=%s", camera_id)
