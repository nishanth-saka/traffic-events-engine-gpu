# app/state.py

import time
from typing import Dict

from app.detection.detection_manager import DetectionManager
from app.ingest.frame.store import frame_store


class AppState:
    """
    Global application state (core services).
    """

    def __init__(self):
        # Concrete frame provider
        self.frames = frame_store

        # Detection metrics + accuracy logging
        self.detection_manager = DetectionManager()


class RuntimeState:
    """
    Lightweight runtime observability state.

    - Safe for concurrent reads
    - Updated by RTSP threads
    - Exposed via debug / runtime APIs
    """

    def __init__(self):
        # cam_id -> bool
        self.rtsp_connected: Dict[str, bool] = {}

        # cam_id -> last frame timestamp
        self.last_frame_ts: Dict[str, float] = {}

        # cam_id -> total frames seen
        self.frame_count: Dict[str, int] = {}

        # process start time
        self.start_time = time.time()


# 🔒 Global singletons
app_state = AppState()
runtime_state = RuntimeState()
