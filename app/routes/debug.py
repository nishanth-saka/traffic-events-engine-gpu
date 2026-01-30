# app/routes/debug.py

import time
from fastapi import APIRouter
from app.state import app_state
from app.events.store import EVENT_STORE

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/pipeline")
def debug_pipeline():
    """
    Read-only pipeline introspection.
    No side effects.
    """

    frames = app_state.frames
    detection_manager = app_state.detection_manager

    cameras = []

    for cam_id in frames.camera_ids():
        frame = frames.get_latest_frame(cam_id)
        detections = detection_manager.get(cam_id)
        events = EVENT_STORE.all()

        cam_events = [e for e in events if e.get("cam_id") == cam_id]

        cameras.append({
            "cam_id": cam_id,
            "frame_present": frame is not None,
            "frame_shape": getattr(frame, "shape", None),
            "detections_count": len(detections),
            "events_count": len(cam_events),
        })

    return {
        "timestamp": time.time(),
        "camera_count": len(cameras),
        "cameras": cameras,
    }
