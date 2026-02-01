# =================================================
# 🔥 PHASE 1 — FORENSIC PYTHON STARTUP LOGGING
# =================================================
import os
import sys

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
import uuid
import logging
from fastapi import FastAPI

from app.config import CAMERAS
from app.shared import app_state

# =================================================
# LOGGING SETUP (GLOBAL, BOOT-ID AWARE)
# =================================================
BOOT_ID = str(uuid.uuid4())[:8]


class BootIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.boot_id = BOOT_ID
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | boot=%(boot_id)s | %(message)s",
    force=True,
)

logging.getLogger().addFilter(BootIdFilter())

logger = logging.getLogger("app.main")
logger.warning("🔥 Logging initialized (boot_id=%s)", BOOT_ID)

# =================================================
# FASTAPI APP
# =================================================
app = FastAPI(title="Traffic Events Engine")

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
    # Plate debug dump (CALIBRATION)
    # -------------------------------
    from fastapi.staticfiles import StaticFiles

    os.makedirs("/tmp/plate_debug", exist_ok=True)

    app.mount(
        "/debug/plates",
        StaticFiles(directory="/tmp/plate_debug"),
        name="plate_debug",
    )

    logger.warning(
        "[Startup] Plate debug mount active → /debug/plates (CALIBRATION MODE)"
    )

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

app.include_router(preview.router)
app.include_router(debug_rtsp.router)

# =================================================
# Railway entrypoint:
#   uvicorn app.main:app
# =================================================
