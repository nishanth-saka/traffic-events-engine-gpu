import asyncio
import logging

from app.ingest.frame.pipeline import process_frame
from app.shared import app_state

logger = logging.getLogger(__name__)


async def ingest_frame_async(
    *,
    camera_id: str,
    frame_ts: float,
    frame,
):
    logger.info("[SERVICE] ingest frame | cam=%s", camera_id)

    # vehicles empty for HTTP ingest (no detection yet)
    return await asyncio.to_thread(
        process_frame,
        camera_id=camera_id,
        frame_ts=frame_ts,
        frame=frame,
        vehicles=[],
        frame_store=app_state.frames,
    )
