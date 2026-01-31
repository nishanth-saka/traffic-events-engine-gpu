# app/main.py

# =================================================
# 🔥 PHASE 1 — FORENSIC PYTHON STARTUP LOGGING
# (SAFE: no app imports, no subprocess, no RTSP)
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
# NORMAL IMPORTS (SAFE ZONE)
# =================================================
import uuid
import logging
from fastapi import FastAPI

from app.config import CAMERAS
from app.shared import app_state

# =================================================
# LOGGING SETUP (Railway-visible)
# =================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    force=True,
)

logger = logging.getLogger("app.main")
logger.warning("🔥 Logging initialized (import phase)")

# =================================================
# FASTAPI APP
# =================================================
app = FastAPI(title="Traffic Events Engine")

# =================================================
# STARTUP — RUNTIME WIRING ONLY
# =================================================
@app.on_event("startup")
def startup():
    print("🔥 STARTUP FUNCTION ENTERED")

    boot_id = str(uuid.uuid4())[:8]
    logger.warning(
        "🔥 STARTUP PROBE 🔥 | boot_id=%s | pid=%s | cwd=%s | PYTHONPATH=%s",
        boot_id,
        os.getpid(),
        os.getcwd(),
        os.getenv("PYTHONPATH"),
    )

    # -------------------------------
    # FrameHub init (lightweight)
    # -------------------------------
    from app.frames.frame_hub import FrameHub

    frame_hub = FrameHub()
    app_state.frame_hub = frame_hub

    for cam_id in CAMERAS.keys():
        frame_hub.register(cam_id)

    logger.info("[Startup] FrameHub initialized & cameras registered")

    # -------------------------------
    # RTSP ingestion (SUB only)
    # -------------------------------
    from app.ingest.rtsp.launcher import RTSPLauncher

    rtsp_launcher = RTSPLauncher(frame_hub)
    app_state.rtsp_launcher = rtsp_launcher

    for cam_id, cam_cfg in CAMERAS.items():
        if "sub" not in cam_cfg:
            logger.warning(
                "[Startup] Camera '%s' missing 'sub' stream, skipping",
                cam_id,
            )
            continue

        rtsp_launcher.add_camera(
            cam_id=cam_id,
            rtsp_url=cam_cfg["sub"],  # 🔒 SUB stream ONLY
        )

    logger.warning("[Startup] RTSP SUB ingestion started")
    logger.warning("[Startup] Minimal startup COMPLETE")

# =================================================
# ROUTES (imported AFTER app + logging)
# =================================================
from app.routes import preview  # noqa: E402
from app.routes import debug_rtsp  # noqa: E402

app.include_router(preview.router)
app.include_router(debug_rtsp.router)

# =================================================
# NOTE:
# Railway uses: uvicorn app.main:app
# __main__ block is NOT relied upon
# =================================================
