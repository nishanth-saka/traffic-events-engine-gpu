from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import time
import numpy as np
import cv2
import logging

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

    - Receives ONE frame
    - Runs detection + ANPR pipeline
    - Emits events
    - Returns lightweight result summary
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
    # Run pipeline
    # -----------------------------
    result = process_frame(
        camera_id=camera_id,
        frame_ts=ts,
        frame=frame,
    )

    return {
        "status": "ok",
        "camera_id": camera_id,
        "frame_ts": ts,
        "result": result,
    }
