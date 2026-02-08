# app/routes/runtime.py

import time
from fastapi import APIRouter
from app.state import runtime_state

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/rtsp")
def rtsp_status():
    """
    🔄 RTSP connection status per camera
    """
    return {
        "rtsp_connected": runtime_state.rtsp_connected,
        "last_frame_ts": runtime_state.last_frame_ts,
    }


@router.get("/metrics")
def metrics():
    """
    📊 Basic runtime metrics
    """
    now = time.time()
    uptime = now - runtime_state.start_time

    fps = {}
    for cam_id, count in runtime_state.frame_count.items():
        fps[cam_id] = round(count / max(uptime, 1), 2)

    return {
        "uptime_sec": round(uptime, 2),
        "frames_per_sec": fps,
        "total_frames": runtime_state.frame_count,
    }


@router.get("/state")
def runtime_state_dump():
    """
    🧠 Full runtime snapshot (deploy sanity check)
    """
    return {
        "uptime_sec": round(time.time() - runtime_state.start_time, 2),
        "rtsp_connected": runtime_state.rtsp_connected,
        "last_frame_ts": runtime_state.last_frame_ts,
        "frame_count": runtime_state.frame_count,
    }
