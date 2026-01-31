# app/routes/preview.py

import time
import logging
import cv2

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.state import app_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preview", tags=["preview"])


@router.get("/stream/{cam_id}")
def mjpeg_preview(cam_id: str):
    camera_manager = app_state.rtsp_launcher

    if not camera_manager.has_camera(cam_id):
        raise HTTPException(status_code=404, detail="Camera not found")

    def frame_generator():
        target_fps = 10.0
        min_interval = 1.0 / target_fps
        last_sent = 0.0

        while True:
            frame = camera_manager.get_latest_frame(cam_id)
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

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
