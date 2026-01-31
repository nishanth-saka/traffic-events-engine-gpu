# app/state.py

import threading
from typing import Dict

from app.rtsp.reader import RTSPReader


class FrameStore:
    """
    Overwrite-only frame store.
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

    def get(self, cam_id: str):
        lock = self._locks.get(cam_id)
        if not lock:
            return None
        with lock:
            return self._frames.get(cam_id)


class AppState:
    """
    Global application state.
    """
    def __init__(self):
        self.frame_store = FrameStore()
        self.rtsp_readers: Dict[str, RTSPReader] = {}

    def add_camera(self, cam_id: str, rtsp_url: str):
        if cam_id in self.rtsp_readers:
            return

        self.frame_store.register(cam_id)

        reader = RTSPReader(
            cam_id=cam_id,
            rtsp_url=rtsp_url,
            frame_store=self.frame_store,
        )

        reader.start()
        self.rtsp_readers[cam_id] = reader

    def get_latest_frame(self, cam_id: str):
        return self.frame_store.get(cam_id)


app_state = AppState()
