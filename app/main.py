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
# Normal imports START HERE
# =================================================
import uuid
import logging
from fastapi import FastAPI


# ---- Guarded import: config ----
try:
    from app.config import CAMERAS
    print("✅ from app.config import CAMERAS SUCCESS")
except Exception as e:
    print("🔥 FAILED importing app.config")
    print("Exception:", repr(e))
    raise


# ---- Guarded import: shared state ----
try:
    from app.shared import app_state
    print("✅ from app.shared import app_state SUCCESS")
except Exception as e:
    print("🔥 FAILED importing app.shared")
    print("Exception:", repr(e))
    raise


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
# Startup — RUNTIME WIRING ONLY
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
    # Initialize FrameHub (REQUIRED)
    # -------------------------------
    from app.frames.frame_hub import FrameHub  # ✅ FIXED PATH

    app_state.frame_hub = FrameHub()

    logger.info("[Startup] FrameHub initialized")
    logger.info("[Startup] Minimal startup complete (no RTSP, no YOLO)")


# =================================================
# Routes
# =================================================
from app.routes import preview  # noqa: E402

app.include_router(preview.router)


# =================================================
# HARD ENTRYPOINT (Railway-safe)
# =================================================
if __name__ == "__main__":
    import uvicorn

    print("🔥 __main__ ENTRYPOINT HIT")
    print("PORT =", os.environ.get("PORT"))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ["PORT"]),
        log_level="info",
        access_log=True,
    )
