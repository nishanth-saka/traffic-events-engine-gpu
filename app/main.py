# app/main.py

import logging

from fastapi import FastAPI

from app.config import CAMERAS
from app.state import app_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# FastAPI app MUST be created first
# -------------------------------------------------
app = FastAPI(title="Traffic Events Engine")

# -------------------------------------------------
# Startup
# -------------------------------------------------
@app.on_event("startup")
def startup():
    logger.info("[Startup] Registering cameras (Stage-2)")

    for cam_id, cfg in CAMERAS.items():
        app_state.add_camera(
            cam_id=cam_id,
            rtsp_url=cfg["main"],
        )

    logger.info("[Startup] Camera registration complete")

# -------------------------------------------------
# Routes
# -------------------------------------------------
# (import AFTER app is defined)
from app.routes import preview  # noqa: E402

app.include_router(preview.router)
