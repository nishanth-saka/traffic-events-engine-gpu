# app/state.py

from app.detection.detection_manager import DetectionManager


class AppState:
    def __init__(self):
        # 🔥 Lazy import to avoid circular dependency
        from app.ingest.frame.pipeline import frame_store

        self.frames = frame_store
        self.detection_manager = DetectionManager()


app_state = AppState()
