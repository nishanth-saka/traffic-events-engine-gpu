# app/ingest/rtsp/launcher.py

import asyncio
import logging

from app.ingest.rtsp.reader import RTSPReader

logger = logging.getLogger("RTSP")

RTSP_CAMERAS = {
    "cam_1": "rtsp://USER:PASSWORD@IP:554/sub_stream",
    # add more cameras here
}


async def start_rtsp_after_delay(delay_sec: int = 5):
    """
    Start RTSP readers AFTER FastAPI startup.

    This prevents slow RTSP connections from blocking deploys.
    """
    logger.info("[RTSP] Delaying RTSP startup by %s seconds", delay_sec)
    await asyncio.sleep(delay_sec)

    logger.info("[RTSP] Starting RTSP readers")

    for cam_id, rtsp_url in RTSP_CAMERAS.items():
        reader = RTSPReader(
            camera_id=cam_id,
            rtsp_url=rtsp_url,
            fps=3,
        )
        reader.start()

        logger.info("[RTSP] RTSPReader started for %s", cam_id)
