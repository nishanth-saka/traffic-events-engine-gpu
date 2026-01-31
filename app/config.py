# app/config.py

import os
import sys

print("\n>>> LOADING app.config")
print(">>> app.config __file__:", __file__)
print(">>> CWD:", os.getcwd())
print(">>> sys.path:")
for p in sys.path:
    print("   -", p)
print(">>> ENV PYTHONPATH:", os.getenv("PYTHONPATH"))
print(">>> ================================\n")

# app/config.py

"""
Central application configuration.

STAGE 1:
- Define cameras explicitly
- MAIN stream only
"""

CAMERAS = {
    "cam_1": {
        "main_rtsp_url": "rtsp://admin:Admin%40123@103.88.236.191:10554/cam/realmonitor?channel=1&subtype=0"
    }
}

# Future-proofing (used in later stages)
DEFAULT_MAIN_RESOLUTION = (1920, 1080)
