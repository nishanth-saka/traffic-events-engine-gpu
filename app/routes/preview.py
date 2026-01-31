# app/routes/preview.py

import time
import logging
import cv2

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response

from app.state import app_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preview", tags=["preview"])


@router.get("/stream/{cam_id}")
def mjpeg_preview(cam_id: str):
    frame_hub = app_state.frame_hub

    # 1️⃣ Camera must be known
    if not frame_hub.has_camera(cam_id):
        raise HTTPException(status_code=404, detail="Camera not found")

    def frame_generator():
        target_fps = 10.0
        min_interval = 1.0 / target_fps
        last_sent = 0.0

        while True:
            frame = frame_hub.get_latest_frame(cam_id)

            # 2️⃣ Camera exists but no frames yet → just wait
            if frame is None:
                time.sleep(0.05)
                continue

            now = time.time()
            if now - last_sent < min_interval:
                time.sleep(0.002)
                continue

            last_sent = now

            success, jpeg = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), 75],
            )

            if not success:
                logger.warning("JPEG encode failed for %s", cam_id)
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg.tobytes()
                + b"\r\n"
            )

    # 3️⃣ If camera exists but never produced frames yet,
    # StreamingResponse will idle safely (no 500s)
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
