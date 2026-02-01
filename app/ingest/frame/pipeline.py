# app/ingest/frame/pipeline.py

import logging
from app.ingest.frame.plate_proposal import propose_plate_regions

logger = logging.getLogger(__name__)

def process_frame(*, camera_id, frame_ts, frame, vehicles, frame_store=None):
    logger.info(
        "[PIPELINE] start | cam=%s vehicles=%d",
        camera_id,
        len(vehicles),
    )

    plate_total = 0

    for idx, vehicle in enumerate(vehicles):
        crop = vehicle.get("crop")
        if crop is None:
            continue

        plates = propose_plate_regions(crop)
        plate_total += len(plates)

        logger.info(
            "[PLATE] cam=%s vehicle_idx=%d candidates=%d",
            camera_id,
            idx,
            len(plates),
        )

        for p_idx, p in enumerate(plates):
            logger.debug(
                "[PLATE_CAND] cam=%s v=%d p=%d area=%.3f aspect=%.2f blur=%.1f skew=%.1f",
                camera_id,
                idx,
                p_idx,
                p["area_ratio"],
                p["aspect"],
                p["blur"],
                p["skew"],
            )

    return {
        "plates": [],   # intentionally unchanged
        "vehicles": vehicles,
    }
