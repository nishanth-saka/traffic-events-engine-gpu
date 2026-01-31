# app/ingest/frame/router.py

import time
import asyncio
import logging
import numpy as np

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.ingest.frame.pipeline import process_frame
from app.shared import app_state  # Updated import to use shared module

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ingest/frame",
    tags=["frame-ingest"],
)

MAX_INFLIGHT = 8
_inflight = 0


@router.post("")
async def ingest_frame(
    camera_id: str = Form(...),
    frame_ts: float | None = Form(None),
    image: UploadFile = File(...),
):
    import cv2  # lazy import

    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=415, detail="Unsupported image type")

    image_bytes = await image.read()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    ts = frame_ts or time.time()

    global _inflight
    if _inflight >= MAX_INFLIGHT:
        raise HTTPException(status_code=429, detail="Too many frames in flight")

    _inflight += 1

    async def _run():
        global _inflight
        try:
            await asyncio.to_thread(
                process_frame,
                camera_id=camera_id,
                frame_ts=ts,
                frame=frame,
                frame_store=app_state.frames,   # 👈 injected here
            )
        finally:
            _inflight -= 1

    asyncio.create_task(_run())

    logger.info("Frame accepted: %s", camera_id)

    return {
        "status": "accepted",
        "camera_id": camera_id,
        "timestamp": ts,
    }
