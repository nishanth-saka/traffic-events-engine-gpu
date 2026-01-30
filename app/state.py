# app/state.py

from app.detection.detection_manager import DetectionManager
from app.ingest.frame.store import frame_store


class AppState:
    def __init__(self):
        # Concrete frame provider
        self.frames = frame_store

        # Detection metrics + accuracy logging
        self.detection_manager = DetectionManager()


# 🔒 Global application state
app_state = AppState()
