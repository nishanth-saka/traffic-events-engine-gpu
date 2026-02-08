# app/frames/frame_hub.py

import threading
import logging

logger = logging.getLogger("FrameHub")


class FrameHub:
    """
    Stage-2 overwrite-only hub.
    MAIN frames only.
    """

    def __init__(self):
        self._frames = {}
        self._locks = {}

    def register(self, cam_id: str):
        if cam_id not in self._locks:
            self._locks[cam_id] = threading.Lock()
            self._frames[cam_id] = None
            logger.info(f"[FrameHub] Registered {cam_id}")

    def update(self, cam_id: str, frame):
        lock = self._locks.get(cam_id)
        if not lock:
            return
        with lock:
            logger.debug(f"[FrameHub] Updating frame for {cam_id}")
            self._frames[cam_id] = frame

    # -------------------------------------------------
    # Read path
    # -------------------------------------------------
    def latest(self, cam_id: str):
        lock = self._locks.get(cam_id)
        if not lock:
            return None
        with lock:
            logger.debug(f"[FrameHub] Retrieving latest frame for {cam_id}")
            return self._frames.get(cam_id)

    # 🔹 Compatibility alias (DetectionWorker expects this)
    def get_latest(self, cam_id: str):
        return self.latest(cam_id)
