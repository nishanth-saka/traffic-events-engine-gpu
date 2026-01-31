# app/main.py

import logging
from fastapi import FastAPI

from app.config import CAMERAS
from app.state import app_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
def startup():
    logger.info("[Startup] Registering cameras (MAIN only)")

    for cam_id, cfg in CAMERAS.items():
        app_state.add_camera(
            cam_id=cam_id,
            rtsp_url=cfg["main_rtsp_url"],
        )
