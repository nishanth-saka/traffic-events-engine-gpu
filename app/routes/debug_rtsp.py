# app/routes/debug_rtsp.py

import subprocess
import logging
from fastapi import APIRouter

router = APIRouter(prefix="/debug", tags=["debug"])
logger = logging.getLogger(__name__)


@router.get("/rtsp")
def debug_rtsp():
    cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", "RTSP_URL_HERE",
        "-t", "5",
        "-f", "null",
        "-"
    ]

    logger.warning("[RTSP-CHECK] Starting RTSP probe from Railway")

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )

        return {
            "returncode": result.returncode,
            "stderr": result.stderr.decode("utf-8")[-3000:],  # last lines
        }

    except Exception as e:
        logger.error("[RTSP-CHECK] Exception", exc_info=True)
        return {"error": str(e)}
