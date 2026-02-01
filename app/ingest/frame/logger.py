# app/ingest/frame/logger.py
import logging

logger = logging.getLogger("FramePipeline")


def log_pipeline_start(cam_id: str, vehicle_count: int):
    logger.info(
        "[PIPELINE] cam=%s vehicles=%d",
        cam_id,
        vehicle_count,
    )


def log_plate_summary(cam_id: str, vehicle_idx: int, count: int):
    logger.info(
        "[PLATE] cam=%s vehicle_idx=%d candidates=%d",
        cam_id,
        vehicle_idx,
        count,
    )


def log_plate_candidates(cam_id: str, vehicle_idx: int, plates: list):
    for idx, p in enumerate(plates):
        logger.debug(
            "[PLATE_CAND] cam=%s v=%d p=%d area=%.3f aspect=%.2f blur=%.1f skew=%.1f",
            cam_id,
            vehicle_idx,
            idx,
            p["area_ratio"],
            p["aspect"],
            p["blur"],
            p["skew"],
        )
