# app/main.py (startup snippet)

from app.state import app_state
from app.config import CAMERAS


@app.on_event("startup")
def startup():
    for cam_id, cfg in CAMERAS.items():
        app_state.rtsp_launcher.add_camera(
            cam_id,
            rtsp_url=cfg["main"],
        )
    print(f"### STARTED RTSP LAUNCHER FOR CAMERAS: {list(CAMERAS.keys())}")