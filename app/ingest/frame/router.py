import time
import asyncio
import logging
import cv2
import numpy as np

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.ingest.frame.pipeline import process_frame

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/frame")
async def ingest_frame(
    camera_id: str = Form(...),
    frame_ts: float | None = Form(None),
    image: UploadFile = File(...),
):
    """
    Stateless frame ingestion endpoint.

    - Accepts a single image
    - Schedules pipeline via asyncio.create_task (Railway-safe)
    - Returns immediately
    """

    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=415, detail="Unsupported image type")

    image_bytes = await image.read()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    ts = frame_ts or time.time()

    # 🔥 GUARANTEED execution (Railway-safe)
    asyncio.create_task(
        asyncio.to_thread(
            process_frame,
            camera_id=camera_id,
            frame_ts=ts,
            frame=frame,
        )
    )

    print("📥 FRAME ACCEPTED", camera_id)

    return {
        "status": "accepted",
        "camera_id": camera_id,
        "timestamp": ts,
    }
