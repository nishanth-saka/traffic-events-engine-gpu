print("🧠 state.py LOADED FROM:", __file__)

# app/state.py

import os
import sys

print("\n>>> LOADING app.state")
print(">>> app.state __file__:", __file__)
print(">>> CWD:", os.getcwd())
print(">>> sys.path:")
for p in sys.path:
    print("   -", p)
print(">>> ================================\n")

from app.frames.frame_hub import FrameHub


class AppState:
    def __init__(self):
        self.frame_hub = FrameHub()
        self.detection_manager = None


app_state = AppState()
