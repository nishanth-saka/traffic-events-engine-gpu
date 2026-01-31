# app/ingest/rtsp/launcher.py

import logging
from app.ingest.rtsp.reader import RTSPReader

logger = logging.getLogger(__name__)


class RTSPLauncher:
    """
    Stage-2 RTSP lifecycle owner.
    MAIN stream only.
    """

    def __init__(self, frame_hub):
        self._readers = {}
        self._frame_hub = frame_hub

    def add_camera(self, cam_id: str, rtsp_url: str, resolution=(1920, 1080)):
        if cam_id in self._readers:
            return

        reader = RTSPReader(
            cam_id=cam_id,
            rtsp_url=rtsp_url,
            frame_hub=self._frame_hub,
            width=resolution[0],
            height=resolution[1],
        )
        self._readers[cam_id] = reader
        reader.start()

        logger.info(f"[RTSPLauncher] Started MAIN stream for {cam_id}")

    def has_camera(self, cam_id: str) -> bool:
        return cam_id in self._readers

    def get_latest_frame(self, cam_id: str):
        return self._frame_hub.latest(cam_id)
