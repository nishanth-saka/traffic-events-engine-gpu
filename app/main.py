# app/main.py
raise RuntimeError("🔥 CACHE BUST TEST: main.py executed")
print("### LOADED MAIN.PY FROM:", __file__)

import logging
from fastapi import FastAPI

from app.config import CAMERAS
from app.state import app_state
from app.ingest.rtsp.launcher import RTSPLauncher

# ---- Stage-3 Lite imports ----
from ultralytics import YOLO
from app.detection.detection_manager import DetectionManager
from app.detection.detection_worker import DetectionWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Traffic Events Engine")

# -------------------------------------------------
# Core runtime objects
# -------------------------------------------------

# RTSP launcher (Stage-2)
rtsp_launcher = RTSPLauncher(app_state.frame_hub)

# Detection manager (Stage-3 Lite)
app_state.detection_manager = DetectionManager()

# -------------------------------------------------
# Startup
# -------------------------------------------------

@app.on_event("startup")
def startup():
    logger.info("[Startup] Registering cameras (Stage-1 / Single MAIN stream)")

    # ---- RTSP startup ----
    for cam_id, cfg in CAMERAS.items():
        if "main_rtsp_url" not in cfg:
            raise RuntimeError(
                f"Camera '{cam_id}' missing required 'main_rtsp_url'"
            )

        rtsp_launcher.add_camera(
            cam_id=cam_id,
            rtsp_url=cfg["main_rtsp_url"],
        )

        logger.info(
            "[Startup] Camera %s: MAIN stream registered",
            cam_id,
        )

    # ---- Stage-3 Lite: Detection ----
    logger.info("[Startup] Starting Stage-3 Lite detection workers")

    # Load YOLO once (shared by all workers)
    yolo_model = YOLO("yolov8n.pt")

    for cam_id in CAMERAS.keys():
        worker = DetectionWorker(
            cam_id=cam_id,
            frame_hub=app_state.frame_hub,
            detection_manager=app_state.detection_manager,
            model=yolo_model,
            fps=3,
            conf=0.4,
        )
        worker.start()

        logger.info(
            "[Startup] Detection worker started for %s",
            cam_id,
        )

    logger.info("[Startup] Startup complete")


# -------------------------------------------------
# Routes
# -------------------------------------------------

from app.routes import preview  # noqa: E402
app.include_router(preview.router)
