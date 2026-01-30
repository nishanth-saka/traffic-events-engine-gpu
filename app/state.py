# app/state.py

from app.detection.detection_manager import DetectionManager
from app.frames.base import FrameStore  # or whatever you already use
# other existing imports stay as-is


class AppState:
    def __init__(self):
        # existing state objects
        self.frames = FrameStore()

        # ✅ ADD THIS LINE
        self.detection_manager = DetectionManager()


# singleton
app_state = AppState()
