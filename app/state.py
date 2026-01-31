# app/state.py

print("### LOADED STATE.PY FROM:", __file__)
print("### STATE.PY HASH CHECK: STAGE2_SINGLE_MAIN")

import threading
from typing import Dict
from app.detection.detection_manager import DetectionManager


class FrameHub:
    """
    Overwrite-only MAIN frame hub.
    Single source of truth for frames.
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
    Global state container.
    NO ingest logic here.
    """

    def __init__(self):
        self.frame_hub = FrameHub()
        self.detection_manager = DetectionManager()


app_state = AppState()
