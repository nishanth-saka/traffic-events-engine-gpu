import time
import logging
import cv2
import numpy as np

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks

from app.ingest.frame.pipeline import process_frame

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/frame")
async def ingest_frame(
    background_tasks: BackgroundTasks,
    camera_id: str = Form(...),
    frame_ts: float | None = Form(None),
    image: UploadFile = File(...),
):
    """
    Stateless frame ingestion endpoint.

    - Accepts a single image frame
    - Schedules detection pipeline in background
    - Returns immediately (async-safe)
    """

    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=415, detail="Unsupported image type")

    # -----------------------------
    # Decode image
    # -----------------------------
    image_bytes = await image.read()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    ts = frame_ts or time.time()

    # -----------------------------
    # 🔥 Schedule pipeline execution
    # -----------------------------
    background_tasks.add_task(
        process_frame,
        camera_id=camera_id,
        frame_ts=ts,
        frame=frame,
    )

    logger.info(
        "[INGEST] Frame accepted | camera_id=%s ts=%s",
        camera_id,
        ts,
    )

    return {
        "status": "accepted",
        "camera_id": camera_id,
        "timestamp": ts,
    }
