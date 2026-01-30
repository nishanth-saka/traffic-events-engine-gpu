# app/main.py

import logging

logging.basicConfig(level=logging.INFO)

# 🔒 EARLY dependency sanity check
try:
    import numpy as np
    logging.info(f"[BOOT] NumPy version = {np.__version__}")
except Exception:
    logging.exception("[BOOT] NumPy import failed")
    raise

from fastapi import FastAPI

from app.routes import debug, events, health
from app.ingest.frame.router import router as ingest_router

# ✅ NEW imports (explicit, no magic)
from app.state import app_state
from app.detection.detector import DetectorWorker
from app.detection.models import VehicleDetector

app = FastAPI(title="Traffic Events Engine")

app.include_router(events.router)
app.include_router(health.router)
app.include_router(ingest_router)
app.include_router(debug.router)

# -------------------------------------------------
# Startup: headless detection engine
# -------------------------------------------------
@app.on_event("startup")
def start_detection_workers():
    logging.info("[BOOT] Starting headless detection workers")

    detector = VehicleDetector()

    # IMPORTANT:
    # FrameStore decides what cameras/streams exist
    for cam_id in app_state.frames.camera_ids():
        worker = DetectorWorker(
            cam_id=cam_id,
            camera_manager=app_state.frames,
            detection_manager=app_state.detection_manager,  # ✅ HERE
            detector_fn=detector.detect,
            fps=3,
        )
        worker.start()

        logging.info("[BOOT] DetectorWorker started for %s", cam_id)
