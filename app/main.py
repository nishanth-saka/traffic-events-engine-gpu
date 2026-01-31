# app/main.py

import logging
from fastapi import FastAPI

import app.config as config
from app.state import app_state

import app.state
print("STATE FILE:", app.state.__file__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
def startup():
    logger.info("[Startup] Loading config from: %s", config.__file__)
    logger.info("[Startup] Config attrs: %s", dir(config))

    if not hasattr(config, "CAMERAS"):
        raise RuntimeError("CAMERAS not defined in app.config")

    logger.info("[Startup] Registering cameras (MAIN only)")

    for cam_id, cfg in config.CAMERAS.items():
        app_state.add_camera(
            cam_id=cam_id,
            rtsp_url=cfg["main_rtsp_url"],
        )
