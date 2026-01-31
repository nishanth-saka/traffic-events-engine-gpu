# app/state.py

import threading
import time
from typing import Dict

from app.ingest.rtsp.reader import RTSPReader
from app.detection.detection_manager import DetectionManager


class FrameHub:
    """
    Stage-2 overwrite-only frame hub.
    MAIN frames only.
    """

    def __init__(self):
        self._frames: Dict[str, any] = {}
        self._locks: Dict[str, threading.Lock] = {}

    def register(self, cam_id: str):
        if cam_id not in self._locks:
            self._locks[cam_id] = threading.Lock()
            self._frames[cam_id] = None

    def update(self, cam_id: str, frame):
        lock = self._locks.get(cam_id)
        if not lock:
            return
        with lock:
            self._frames[cam_id] = frame

    def get_latest(self, cam_id: str):
        lock = self._locks.get(cam_id)
        if not lock:
            return None
        with lock:
            return self._frames.get(cam_id)


class AppState:
    """
    Global application state (Stage-2).

    - Owns RTSP lifecycle
    - Owns MAIN FrameHub
    - Detection + Preview read same frames
    """

    def __init__(self):
        self.frame_hub = FrameHub()
        self.detection_manager = DetectionManager()
        self._rtsp_readers: Dict[str, RTSPReader] = {}

    # -------------------------------------------------
    # Camera lifecycle
    # -------------------------------------------------
    def add_camera(self, cam_id: str, rtsp_url: str):
        if cam_id in self._rtsp_readers:
            return

        self.frame_hub.register(cam_id)

        reader = RTSPReader(
            cam_id=cam_id,
            rtsp_url=rtsp_url,
            frame_store=self.frame_hub,  # 🔑 same hub for all consumers
        )

        reader.start()
        self._rtsp_readers[cam_id] = reader

    def has_camera(self, cam_id: str) -> bool:
        return cam_id in self._rtsp_readers

    # -------------------------------------------------
    # Frame access (MAIN only)
    # -------------------------------------------------
    def get_latest_frame(self, cam_id: str):
        return self.frame_hub.get_latest(cam_id)


app_state = AppState()
