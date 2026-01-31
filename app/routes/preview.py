# app/routes/preview.py

import time
import cv2

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.state import app_state

router = APIRouter(prefix="/preview")


@router.get("/stream/{cam_id}")
def preview(cam_id: str):
    if not app_state.rtsp_launcher.has_camera(cam_id):
        raise HTTPException(status_code=404, detail="Camera not found")

    def gen():
        while True:
            frame = app_state.rtsp_launcher.get_latest_frame(cam_id)
            if frame is None:
                time.sleep(0.05)
                continue

            ok, jpeg = cv2.imencode(".jpg", frame)
            if not ok:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg.tobytes()
                + b"\r\n"
            )

    return StreamingResponse(
        gen(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
