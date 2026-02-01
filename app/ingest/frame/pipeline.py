# app/ingest/frame/pipeline.py
import logging

logger = logging.getLogger(__name__)

def process_frame(*, camera_id, frame_ts, frame, vehicles, frame_store=None):
    logger.info(
        "[PIPELINE] start | cam=%s vehicles=%d",
        camera_id,
        len(vehicles),
    )

    return {
        "plates": [],
        "vehicles": vehicles,
    }
