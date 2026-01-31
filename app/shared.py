# app/shared.py

class AppState:
    def __init__(self):
        # Filled during FastAPI startup
        self.frame_hub = None
        self.detection_manager = None

# 🔒 Singleton: created exactly once, at import time
app_state = AppState()

__all__ = ["app_state"]
