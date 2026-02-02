# app/ingest/frame/pipeline.py

import logging

from app.ingest.frame.types import Vehicle
from app.ingest.frame.plate_proposal import propose_plate_regions
from app.ingest.frame.logger import (
    log_pipeline_start,
    log_plate_summary,
    log_plate_candidates,
)
from app.ingest.frame.ocr import run_ocr
from app.ingest.frame.quality_gate import cheap_plate_gate
from app.ingest.frame.debug_dump import maybe_dump_plate_crop
from app.ingest.frame.events import emit_event
from app.ingest.frame.policy import (
    CALIBRATION_PLATE_POLICY,
    CANDIDATE_CONF_THRESHOLD,
    CONFIRMED_CONF_THRESHOLD,
    ENABLE_HEAVY_OCR,
)

logger = logging.getLogger(__name__)


def run_frame_pipeline(*, camera_id, frame_ts, frame, vehicles):
    """
    Gate-2 frame pipeline.

    Vehicle →
      Plate proposals →
        Cheap gate →
          OCR →
            Confidence gate →
              Event emission
    """

    log_pipeline_start(camera_id, len(vehicles))

    for v_idx, v in enumerate(vehicles):
        vehicle = Vehicle.from_detection(v, frame)

        # --------------------------------------------
        # Defensive guards
        # --------------------------------------------
        if vehicle.crop is None:
            logger.debug(
                "[PIPELINE] skip vehicle | cam=%s vehicle=%d reason=no_crop",
                camera_id,
                v_idx,
            )
            continue

        h, w = vehicle.crop.shape[:2]
        if h < 40 or w < 80:
            logger.debug(
                "[PIPELINE] skip vehicle | cam=%s vehicle=%d reason=small_crop h=%d w=%d",
                camera_id,
                v_idx,
                h,
                w,
            )
            continue

        # --------------------------------------------
        # Gate-2: plate proposals (metrics only)
        # --------------------------------------------
        plates = propose_plate_regions(
            vehicle.crop,
            policy=CALIBRATION_PLATE_POLICY,
        )

        log_plate_summary(camera_id, v_idx, len(plates))
        log_plate_candidates(camera_id, v_idx, plates)

        # --------------------------------------------
        # OCR gated flow
        # --------------------------------------------
        for p_idx, plate in enumerate(plates):
            try:
                # -------------------------
                # Gate 1 — cheap reject
                # -------------------------
                if not cheap_plate_gate(plate):
                    logger.debug(
                        "[PLATE-GATE] reject | cam=%s vehicle=%d plate=%d reason=cheap_gate",
                        camera_id,
                        v_idx,
                        p_idx,
                    )
                    continue

                # -------------------------
                # Debug dump (only passed plates)
                # -------------------------
                maybe_dump_plate_crop(
                    cam_id=camera_id,
                    frame_ts=frame_ts,
                    vehicle_idx=v_idx,
                    plate_idx=p_idx,
                    vehicle_crop=vehicle.crop,
                    plate_crop=plate["crop"],
                    bbox=plate.get("bbox"),
                )

                # -------------------------
                # Gate 2 — LIGHT OCR
                # -------------------------
                ocr = run_ocr(plate["crop"], mode="light")

                logger.info(
                    "[OCR] cam=%s vehicle=%d plate=%d text=%r conf=%.3f",
                    camera_id,
                    v_idx,
                    p_idx,
                    ocr.text,
                    ocr.confidence,
                )

                # -------------------------
                # Gate 3 — confidence decision
                # -------------------------
                if ocr.confidence >= CONFIRMED_CONF_THRESHOLD:
                    emit_event(
                        "plate.confirmed",
                        camera_id=camera_id,
                        vehicle_idx=v_idx,
                        plate_idx=p_idx,
                        plate=ocr.text,
                        confidence=ocr.confidence,
                    )
                    continue

                if ocr.confidence >= CANDIDATE_CONF_THRESHOLD:
                    emit_event(
                        "plate.candidate",
                        camera_id=camera_id,
                        vehicle_idx=v_idx,
                        plate_idx=p_idx,
                        plate=ocr.text,
                        confidence=ocr.confidence,
                    )
                    continue

                # -------------------------
                # Gate 4 — optional escalation
                # -------------------------
                if ENABLE_HEAVY_OCR:
                    heavy = run_ocr(plate["crop"], mode="heavy")

                    logger.info(
                        "[OCR-HEAVY] cam=%s vehicle=%d plate=%d text=%r conf=%.3f",
                        camera_id,
                        v_idx,
                        p_idx,
                        heavy.text,
                        heavy.confidence,
                    )

                    if heavy.confidence >= CONFIRMED_CONF_THRESHOLD:
                        emit_event(
                            "plate.confirmed",
                            camera_id=camera_id,
                            vehicle_idx=v_idx,
                            plate_idx=p_idx,
                            plate=heavy.text,
                            confidence=heavy.confidence,
                        )

            except Exception as e:
                logger.exception(
                    "[OCR] failure | cam=%s vehicle=%d plate=%d err=%s",
                    camera_id,
                    v_idx,
                    p_idx,
                    e,
                )

    return {
        "vehicles": vehicles,
        "plates": [],  # emitted via events only
    }
