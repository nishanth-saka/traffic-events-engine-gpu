# app/routes/system.py

import os
import time
from fastapi import APIRouter

router = APIRouter(tags=["system"])

_START_TS = time.monotonic()

@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "traffic-events-engine",
        "pid": os.getpid(),
        "uptime_s": int(time.monotonic() - _START_TS),
    }
