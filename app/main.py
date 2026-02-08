# app/main.py

# =================================================
# 🔥 PHASE 1 — FORENSIC PYTHON STARTUP LOGGING
# =================================================
import os
import shutil
import sys
import uuid
import logging

FORENSIC_STARTUP = True

if FORENSIC_STARTUP:
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
# NORMAL IMPORTS
# =================================================
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import CAMERAS
from app.shared import app_state

logger = logging.getLogger(__name__)

# =================================================
# 🔥 Startup cleanup (Gate-2 debug)
# =================================================
PLATE_DEBUG_DIR = "/tmp/plate_debug"

try:
    shutil.rmtree(PLATE_DEBUG_DIR, ignore_errors=True)
    os.makedirs(PLATE_DEBUG_DIR, exist_ok=True)

    print(
        f"[STARTUP] Cleared plate debug dir: {PLATE_DEBUG_DIR}",
        flush=True,
    )

    files = os.listdir(PLATE_DEBUG_DIR)
    jpgs = [f for f in files if f.lower().endswith(".jpg")]

    print(
        f"[STARTUP] Plate debug dir verification: "
        f"{len(files)} files, {len(jpgs)} JPGs → {files}",
        flush=True,
    )

except Exception as e:
    print(
        f"[STARTUP] Plate debug cleanup/verify FAILED: {e}",
        flush=True,
    )

# =================================================
# LOGGING SETUP (GLOBAL, BOOT-ID SAFE)
# =================================================
BOOT_ID = str(uuid.uuid4())[:8]

_old_factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs):
    record = _old_factory(*args, **kwargs)
    record.boot_id = BOOT_ID
    return record


logging.setLogRecordFactory(record_factory)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | boot=%(boot_id)s | %(message)s",
    force=True,
)

logger = logging.getLogger("app.main")
logger.warning("🔥 Logging initialized (boot_id=%s)", BOOT_ID)

# =================================================
# FASTAPI APP (AUTHORITATIVE APP OBJECT)
# =================================================
app = FastAPI(title="Traffic Events Engine")

# -------------------------------------------------
# 🔎 DEBUG: plate dump browser (TOP-LEVEL ONLY)
# -------------------------------------------------
os.makedirs(PLATE_DEBUG_DIR, exist_ok=True)

# app.mount(
#     "/debug/plates",
#     StaticFiles(directory=PLATE_DEBUG_DIR),
#     name="plate_debug",
# )

app.mount("/debug/plates/fs", StaticFiles(directory=PLATE_DEBUG_DIR), name="plate_debug")

logger.warning(
    "🖼️ Debug plate browser mounted → /debug/plates"
)

# =================================================
# STARTUP — RUNTIME WIRING ONLY
# =================================================
@app.on_event("startup")
def startup():
    logger.warning(
        "🔥 STARTUP ENTERED | pid=%s | cwd=%s | PYTHONPATH=%s",
        os.getpid(),
        os.getcwd(),
        os.getenv("PYTHONPATH"),
    )

    # -------------------------------
    # FrameHub init (MAIN frames)
    # -------------------------------
    from app.frames.frame_hub import FrameHub

    frame_hub = FrameHub()
    app_state.frame_hub = frame_hub

    for cam_id in CAMERAS.keys():
        frame_hub.register(cam_id)

    logger.info("[Startup] FrameHub initialized & cameras registered")

    # -------------------------------
    # RTSP ingestion (SUB stream ONLY)
    # -------------------------------
    from app.ingest.rtsp.launcher import RTSPLauncher

    rtsp_launcher = RTSPLauncher(frame_hub)
    app_state.rtsp_launcher = rtsp_launcher

    for cam_id, cam_cfg in CAMERAS.items():
        if "sub" not in cam_cfg:
            logger.warning(
                "[Startup] Camera '%s' missing SUB stream → skipped",
                cam_id,
            )
            continue

        rtsp_launcher.add_camera(
            cam_id=cam_id,
            rtsp_url=cam_cfg["sub"],  # 🔒 SUB stream only (by design)
        )

        logger.warning(
            "[Startup] RTSP SUB stream wired | cam=%s",
            cam_id,
        )

    logger.warning(
        "[Startup] RTSP ingestion LIVE (SUB stream, OCR calibration expected to fail)"
    )

    # -------------------------------
    # Detection Manager + Workers
    # -------------------------------
    from app.detection.detection_manager import DetectionManager
    from app.detection.detector import DetectionWorker

    detection_manager = DetectionManager()
    app_state.detection_manager = detection_manager

    for cam_id in CAMERAS.keys():
        worker = DetectionWorker(
            cam_id=cam_id,
            frame_hub=frame_hub,
            detection_manager=detection_manager,
            fps=2,
        )
        worker.start()

        logger.warning(
            "[Startup] DetectionWorker started | cam=%s",
            cam_id,
        )

    logger.warning(
        "[Startup] STAGE-1 COMPLETE ✅ | Vehicle detection live | OCR = calibration only"
    )

# =================================================
# ROUTES
# =================================================
from app.routes import preview  # noqa: E402
from app.routes import debug_rtsp  # noqa: E402
from app.routes import debug_plates  # noqa: E402
from app.routes import system  # noqa: E402

app.include_router(preview.router)
app.include_router(debug_rtsp.router)
app.include_router(debug_plates.router)
app.include_router(system.router)

# =================================================
# Railway entrypoint:
#   uvicorn app.main:app
# =================================================
