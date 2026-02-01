import logging

from app.ingest.frame.types import Vehicle
from app.ingest.frame.plate_proposal import propose_plate_regions
from app.ingest.frame.logger import (
    log_pipeline_start,
    log_plate_summary,
    log_plate_candidates,
)
from app.ingest.frame.ocr import run_ocr

logger = logging.getLogger(__name__)


def run_frame_pipeline(*, camera_id, frame_ts, frame, vehicles):
    """
    Gate-2 frame pipeline.
    Vehicle → Plate proposals → OCR calibration
    """

    log_pipeline_start(camera_id, len(vehicles))

    for idx, v in enumerate(vehicles):
        vehicle = Vehicle.from_detection(v, frame)

        # ============================================
        # 🛡️ DEFENSIVE: skip if vehicle crop is invalid
        # ============================================
        if vehicle.crop is None:
            logger.warning(
                "[PIPELINE] skip vehicle | cam=%s vehicle=%d reason=no_crop",
                camera_id,
                idx,
            )
            continue

        h, w = vehicle.crop.shape[:2]
        if h < 40 or w < 80:
            logger.warning(
                "[PIPELINE] skip vehicle | cam=%s vehicle=%d reason=small_crop h=%d w=%d",
                camera_id,
                idx,
                h,
                w,
            )
            continue

        # 🔓 Gate-2 calibration policy
        from app.ingest.frame.policy import CALIBRATION_PLATE_POLICY

        plates = propose_plate_regions(
            vehicle.crop,
            policy=CALIBRATION_PLATE_POLICY,
        )

        log_plate_summary(camera_id, idx, len(plates))
        log_plate_candidates(camera_id, idx, plates)

        # ============================================
        # 🔥 STEP 1 — FORCE OCR (CALIBRATION MODE)
        # ============================================
        for p_idx, plate in enumerate(plates):
            try:
                logger.warning(
                    "[OCR-CALIBRATION] attempting OCR | cam=%s vehicle=%d plate=%d",
                    camera_id,
                    idx,
                    p_idx,
                )

                ocr_result = run_ocr(plate["crop"])

                logger.warning(
                    "[OCR-CALIBRATION] result | cam=%s vehicle=%d plate=%d text=%r conf=%.3f",
                    camera_id,
                    idx,
                    p_idx,
                    getattr(ocr_result, "text", None),
                    getattr(ocr_result, "confidence", -1.0),
                )

            except Exception as e:
                logger.exception(
                    "[OCR-CALIBRATION] OCR failed | cam=%s vehicle=%d plate=%d err=%s",
                    camera_id,
                    idx,
                    p_idx,
                    e,
                )

    return {
        "vehicles": vehicles,
        "plates": [],  # intentionally not emitted yet
    }
