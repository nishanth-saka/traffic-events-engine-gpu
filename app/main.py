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
        # 🔒 Stage-2 invariant: ONLY sub stream
        rtsp_launcher.add_camera(
            cam_id=cam_id,
            rtsp_url=cfg["sub"],
        )

        logger.info(
            f"[Startup] Camera {cam_id}: SUB stream registered (MAIN disabled)"
        )

    logger.info("[Startup] Startup complete")


from app.routes import preview  # noqa: E402
app.include_router(preview.router)
