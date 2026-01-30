# app/state.py

from app.detection.detection_manager import DetectionManager
from app.ingest.frame.pipeline import frame_store


class AppState:
    def __init__(self):
        # Concrete frame provider (headless)
        self.frames = frame_store

        # Detection metrics + accuracy logging
        self.detection_manager = DetectionManager()


# singleton
app_state = AppState()
