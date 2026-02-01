import os
import time
import cv2
import logging
from typing import Tuple, Optional

logger = logging.getLogger("PlateDebugDump")

# ---- CONFIG ----
DUMP_DIR = "/tmp/plate_dumps"
DUMP_INTERVAL_SEC = 10.0  # throttle: 1 image / cam / 10s

_last_dump_ts = {}  # cam_id -> timestamp


def maybe_dump_plate_crop(
    *,
    cam_id: str,
    frame_ts: float,
    vehicle_crop,
    bbox: Tuple[int, int, int, int],
):
    """
    Dump ONE plate crop image to disk (throttled per camera).
    Safe, silent, best-effort only.
    """

    if vehicle_crop is None or bbox is None:
        return

    now = time.time()
    last_ts = _last_dump_ts.get(cam_id, 0.0)

    if now - last_ts < DUMP_INTERVAL_SEC:
        return

    x, y, w, h = bbox
    if w <= 0 or h <= 0:
        return

    try:
        plate_crop = vehicle_crop[y : y + h, x : x + w]
        if plate_crop.size == 0:
            return

        os.makedirs(DUMP_DIR, exist_ok=True)

        fname = f"{cam_id}_{int(frame_ts)}.jpg"
        path = os.path.join(DUMP_DIR, fname)

        cv2.imwrite(path, plate_crop)

        _last_dump_ts[cam_id] = now

        logger.warning(
            "[PLATE_DUMP] cam=%s path=%s",
            cam_id,
            path,
        )

    except Exception as e:
        logger.error("[PLATE_DUMP] failed cam=%s err=%s", cam_id, e)
