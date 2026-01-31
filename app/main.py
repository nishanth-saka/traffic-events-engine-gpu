# app/main.py

import logging
import threading
import time
import asyncio

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

from app.state import app_state
from app.events.engine import EventsEngine
from app.ingest.rtsp.launcher import start_rtsp_after_delay


# -------------------------------------------------
# FastAPI app
# -------------------------------------------------
app = FastAPI(title="Traffic Events Engine")

# -------------------------------------------------
# Routers
# -------------------------------------------------
app.include_router(events.router)
app.include_router(health.router)
app.include_router(ingest_router)   # optional (testing)
app.include_router(debug.router)

# -------------------------------------------------
# Startup: delayed RTSP startup (NON-BLOCKING)
# -------------------------------------------------
@app.on_event("startup")
async def delayed_rtsp_startup():
    logger.info("[BOOT] Scheduling delayed RTSP startup")
    asyncio.create_task(start_rtsp_after_delay(delay_sec=5))

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
            time.sleep(0.5)

    threading.Thread(
        target=event_loop,
        daemon=True,
        name="EventsEngineLoop",
    ).start()

    logger.info("[BOOT] EventsEngine loop started")
