# app/shared.py

# Initialize app_state here to avoid circular imports
class AppState:
    def __init__(self):
        self.frame_hub = None  # Example attribute
        self.detection_manager = None  # Example attribute

# Create a global instance of AppState
app_state = AppState()

# Export app_state for shared usage
__all__ = ["app_state"]