# app/ingest/rtsp/launcher.py

from typing import Dict
from app.ingest.rtsp.reader import RTSPReader
import threading
import logging

logger = logging.getLogger("RTSPLauncher")


class RTSPLauncher:
    """
    RTSP lifecycle manager (Stage-2).
    """

    def __init__(self, frame_hub):
        self._readers: Dict[str, RTSPReader] = {}
        self.frame_hub = frame_hub

    def add_camera(self, cam_id: str, rtsp_url: str):
        if cam_id in self._readers:
            return

        def initialize_reader():
            try:
                reader = RTSPReader(
                    cam_id=cam_id,
                    rtsp_url=rtsp_url,
                    frame_hub=self.frame_hub,
                )
                self._readers[cam_id] = reader
                reader.start()
            except Exception as e:
                logger.error(f"Failed to initialize RTSPReader for cam_id={cam_id}: {e}")

        thread = threading.Thread(target=initialize_reader, daemon=True)
        thread.start()

    def has_camera(self, cam_id: str) -> bool:
        return cam_id in self._readers

    def get_latest_frame(self, cam_id: str):
        return self.frame_hub.latest(cam_id)
