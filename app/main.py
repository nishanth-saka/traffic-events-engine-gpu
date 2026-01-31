# app/main.py

# =================================================
# 🔥 PHASE 1 — FORENSIC PYTHON STARTUP LOGGING
# =================================================
import os
import sys

print("\n========== PYTHON STARTUP DEBUG ==========")
print("CWD:", os.getcwd())
print("__file__:", __file__)
print("sys.executable:", sys.executable)
print("sys.argv:", sys.argv)

print("\n--- sys.path ---")
for p in sys.path:
    print("  -", p)

print("\n--- Filesystem probes ---")
for path in ["/", "/app", "/app/app"]:
    try:
        print(f"ls {path} ->", os.listdir(path))
    except Exception as e:
        print(f"ls {path} FAILED:", repr(e))

print("\n--- Import sanity checks ---")
try:
    import app
    print("✅ import app SUCCESS:", app)
    print("   app.__file__:", getattr(app, "__file__", None))
except Exception as e:
    print("❌ import app FAILED:", repr(e))

print("==========================================\n")
# =================================================


# =================================================
# Normal imports START HERE (guarded)
# =================================================
import time
import uuid
import logging
from fastapi import FastAPI

# ---- Guarded import: app.config ----
try:
    from app.config import CAMERAS
    print("✅ from app.config import CAMERAS SUCCESS")
except Exception as e:
    print("🔥 FAILED importing app.config")
    print("Exception:", repr(e))
    raise

# ---- Guarded import: app.state ----
try:
    from app.state import app_state
    print("✅ from app.state import app_state SUCCESS")
except Exception as e:
    print("🔥 FAILED importing app.state")
    print("Exception:", repr(e))
    raise

# ---- RTSP + Detection imports ----
from app.ingest.rtsp.launcher import RTSPLauncher
from ultralytics import YOLO
from app.detection.detection_manager import DetectionManager
from app.detection.detection_worker import DetectionWorker


# =================================================
# Logging setup
# =================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =================================================
# FastAPI app
# =================================================
app = FastAPI(title="Traffic Events Engine")


# =================================================
# Core runtime objects
# =================================================
rtsp_launcher = RTSPLauncher(app_state.frame_hub)
app_state.detection_manager = DetectionManager()
APP_START_TIME = time.time()


# =================================================
# Startup
# =================================================
@app.on_event("startup")
def startup():
    boot_id = str(uuid.uuid4())[:8]

    logger.warning(
        "🔥 STARTUP PROBE 🔥 | boot_id=%s | pid=%s | cwd=%s | PYTHONPATH=%s",
        boot_id,
        os.getpid(),
        os.getcwd(),
        os.getenv("PYTHONPATH"),
    )

    logger.info("[Startup] Registering cameras")

    for cam_id, cfg in CAMERAS.items():
        if "main_rtsp_url" not in cfg:
            raise RuntimeError(
                f"Camera '{cam_id}' missing required 'main_rtsp_url'"
            )

        rtsp_launcher.add_camera(
            cam_id=cam_id,
            rtsp_url=cfg["main_rtsp_url"],
        )

        logger.info("[Startup] Camera %s registered", cam_id)

    logger.info("[Startup] Loading YOLO model")
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

        logger.info("[Startup] Detection worker started for %s", cam_id)

    logger.info("[Startup] Startup complete")


# =================================================
# Routes
# =================================================
from app.routes import preview  # noqa: E402
app.include_router(preview.router)
