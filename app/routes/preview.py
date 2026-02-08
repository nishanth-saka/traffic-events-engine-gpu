import time
import logging
import cv2

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.shared import app_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preview", tags=["preview"])


@router.get("/stream/{cam_id}")
def mjpeg_preview(cam_id: str):
    frame_hub = app_state.frame_hub

    if frame_hub is None:
        raise HTTPException(status_code=503, detail="Frame hub not ready")

    def frame_generator():
        target_fps = 10.0
        delay = 1.0 / target_fps

        logger.warning("[MJPEG] generator started for %s", cam_id)

        while True:
            frame = frame_hub.latest(cam_id)

            if frame is None:
                time.sleep(0.05)
                continue

            success, jpeg = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), 75],
            )

            if not success:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Cache-Control: no-cache, no-store, must-revalidate\r\n"
                b"Pragma: no-cache\r\n\r\n"
                + jpeg.tobytes()
                + b"\r\n"
            )

            time.sleep(delay)

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
