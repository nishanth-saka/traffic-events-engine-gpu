# app/main.py

print("### LOADED MAIN.PY FROM:", __file__)

import logging
from fastapi import FastAPI
from app.config import CAMERAS
from app.state import app_state
from app.ingest.rtsp.launcher import RTSPLauncher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Traffic Events Engine")

# 🔑 Create launcher HERE (one-way dependency)
rtsp_launcher = RTSPLauncher(app_state.frame_hub)


@app.on_event("startup")
def startup():
    logger.info("[Startup] Registering cameras (Stage-2)")

    for cam_id, cfg in CAMERAS.items():
        rtsp_launcher.add_camera(
            cam_id=cam_id,
            rtsp_url=cfg["main"],
        )

    logger.info("[Startup] Startup complete")


from app.routes import preview  # noqa: E402
app.include_router(preview.router)
