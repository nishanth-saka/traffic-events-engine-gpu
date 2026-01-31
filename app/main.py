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
import time
import threading
import logging
import numpy as np
from fastapi import FastAPI


# ---- Guarded import: config ----
from app.config import CAMERAS
from app.shared import app_state


# =================================================
# Logging setup
# =================================================
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
    # Initialize FrameHub (ONCE)
    # -------------------------------
    from app.frames.frame_hub import FrameHub

    frame_hub = FrameHub()
    app_state.frame_hub = frame_hub

    # -------------------------------
    # Register cameras
    # -------------------------------
    for cam_id in CAMERAS.keys():
        frame_hub.register(cam_id)

    logger.info("[Startup] FrameHub initialized and cameras registered")

    # -------------------------------
    # Fake frame producer (DEBUG)
    # -------------------------------
    def fake_frames():
        t = 0
        while True:
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)

            # animated content so you KNOW it's live
            frame[:, :] = (0, 180, 0)
            cv = (t % 600)
            frame[100:200, cv:cv + 200] = (255, 255, 255)

            frame_hub.update("cam_1", frame)

            t += 10
            time.sleep(0.1)

    threading.Thread(target=fake_frames, daemon=True).start()

    logger.info("[Startup] Fake frame generator started")
    logger.info("[Startup] Minimal startup complete (DEBUG MODE)")


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
