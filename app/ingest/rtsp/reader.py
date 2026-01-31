# app/ingest/rtsp/reader.py
import cv2
import time
import threading
import logging

from app.ingest.frame.pipeline import process_frame
from app.state import app_state

logger = logging.getLogger("RTSP")


class RTSPReader(threading.Thread):
    def __init__(self, *, camera_id: str, rtsp_url: str, fps: int = 3):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.interval = 1.0 / fps
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(self.rtsp_url)

        if not cap.isOpened():
            logger.error("[RTSP] Failed to open %s", self.rtsp_url)
            return

        logger.info("[RTSP] Connected: %s", self.camera_id)

        while self.running:
            ok, frame = cap.read()
            if not ok:
                logger.warning("[RTSP] Frame read failed: %s", self.camera_id)
                time.sleep(1)
                continue

            ts = time.time()

            try:
                process_frame(
                    camera_id=self.camera_id,
                    frame_ts=ts,
                    frame=frame,
                    frame_store=app_state.frames,
                )
            except Exception:
                logger.exception("[RTSP] Processing failed")

            time.sleep(self.interval)

        cap.release()
