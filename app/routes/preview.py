# app/routes/preview.py

import time
import logging
import cv2

from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response

from app.state import app_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preview", tags=["preview"])


@router.get("/stream/{cam_id}")
def mjpeg_preview(cam_id: str):
    frame_hub = app_state.frame_hub

    def frame_generator():
        target_fps = 10.0
        min_interval = 1.0 / target_fps
        last_sent = 0.0

        while True:
            try:
                frame = frame_hub.get_latest_frame(cam_id)
            except Exception as e:
                logger.exception("FrameHub error for %s", cam_id)
                return

            # No frames yet → just wait
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
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg.tobytes()
                + b"\r\n"
            )

    # IMPORTANT:
    # - No camera existence check
    # - No exceptions raised
    # - Always returns a valid response
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
