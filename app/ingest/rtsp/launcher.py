# app/ingest/rtsp/launcher.py

from typing import Dict
from app.ingest.rtsp.reader import RTSPReader


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

        reader = RTSPReader(
            cam_id=cam_id,
            rtsp_url=rtsp_url,
            frame_hub=self.frame_hub,
        )

        reader.start()  # 🔑 start reader thread
        self._readers[cam_id] = reader

    def has_camera(self, cam_id: str) -> bool:
        return cam_id in self._readers

    def get_latest_frame(self, cam_id: str):
        return self.frame_hub.get_latest(cam_id)
