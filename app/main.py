# app/main.py

import logging
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# 🔒 EARLY dependency sanity check
# -------------------------------------------------
try:
    import numpy as np
    logger.info("[BOOT] NumPy version = %s", np.__version__)
except Exception:
    logger.exception("[BOOT] NumPy import failed")
    raise

from fastapi import FastAPI

from app.routes import debug, events, health
from app.ingest.frame.router import router as ingest_router
from app.ingest.rtsp.reader import RTSPReader

from app.state import app_state
from app.events.engine import EventsEngine


# -------------------------------------------------
# FastAPI app
# -------------------------------------------------
app = FastAPI(title="Traffic Events Engine")

# -------------------------------------------------
# Routers (HTTP ingress + debug)
# -------------------------------------------------
app.include_router(events.router)
app.include_router(health.router)
app.include_router(ingest_router)   # optional: keep for testing
app.include_router(debug.router)

# -------------------------------------------------
# RTSP camera configuration
# -------------------------------------------------
RTSP_CAMERAS = {
    "cam_1": "rtsp://admin:Admin%40123@103.88.236.191:10554/cam/realmonitor?channel=1&subtype=1",
    # "cam_2": "rtsp://...",
}

# -------------------------------------------------
# Startup: RTSP readers (PRIMARY frame source)
# -------------------------------------------------
@app.on_event("startup")
def start_rtsp_readers():
    logger.info("[BOOT] Starting RTSP readers")

    for cam_id, rtsp_url in RTSP_CAMERAS.items():
        reader = RTSPReader(
            camera_id=cam_id,
            rtsp_url=rtsp_url,
            fps=3,   # detection FPS (NOT stream FPS)
        )
        reader.start()

        logger.info("[BOOT] RTSPReader started for %s", cam_id)

# -------------------------------------------------
# Startup: Events engine loop
# -------------------------------------------------
@app.on_event("startup")
def start_event_engine():
    logger.info("[BOOT] Starting EventsEngine loop")

    engine = EventsEngine(app_state.detection_manager)

    def event_loop():
        while True:
            for cam_id in app_state.frames.camera_ids():
                engine.process_camera(cam_id)
            time.sleep(0.5)  # safe, low-frequency loop

    threading.Thread(
        target=event_loop,
        daemon=True,
        name="EventsEngineLoop",
    ).start()

    logger.info("[BOOT] EventsEngine loop started")
