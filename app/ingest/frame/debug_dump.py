import os
import time
import cv2
import logging
from typing import Tuple

logger = logging.getLogger("PlateDebugDump")

# ---- CONFIG ----
DUMP_DIR = "/tmp/plate_debug"
DUMP_INTERVAL_SEC = 10.0  # throttle: 1 image / cam / 10s

_last_dump_ts = {}  # cam_id -> timestamp


def maybe_dump_plate_crop(
    *,
    cam_id: str,
    frame_ts: float,
    vehicle_idx: int,
    plate_idx: int,
    vehicle_crop,
    plate_crop,
    bbox: Tuple[int, int, int, int],
):
    """
    Dump ONE OCR-correlated plate debug image (throttled per camera).

    Image layout:
    - Top: vehicle crop with plate bbox
    - Bottom: plate crop (upsized)
    """

    if vehicle_crop is None or plate_crop is None or bbox is None:
        return

    now = time.time()
    last_ts = _last_dump_ts.get(cam_id, 0.0)

    if now - last_ts < DUMP_INTERVAL_SEC:
        return

    try:
        os.makedirs(DUMP_DIR, exist_ok=True)

        # Draw bbox on vehicle crop
        vis = vehicle_crop.copy()
        x1, y1, x2, y2 = bbox
        cv2.rectangle(
            vis,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2,
        )

        # Resize plate crop to vehicle width for readability
        plate_vis = cv2.resize(
            plate_crop,
            (vis.shape[1], plate_crop.shape[0]),
            interpolation=cv2.INTER_CUBIC,
        )

        combined = cv2.vconcat([vis, plate_vis])

        fname = (
            f"cam={cam_id}_"
            f"veh={vehicle_idx}_"
            f"plate={plate_idx}_"
            f"ts={int(frame_ts)}.jpg"
        )

        path = os.path.join(DUMP_DIR, fname)
        cv2.imwrite(path, combined)

        _last_dump_ts[cam_id] = now

        logger.warning(
            "[PLATE_DUMP] cam=%s vehicle=%d plate=%d path=%s",
            cam_id,
            vehicle_idx,
            plate_idx,
            path,
        )

    except Exception as e:
        logger.error(
            "[PLATE_DUMP] failed cam=%s vehicle=%d plate=%d err=%s",
            cam_id,
            vehicle_idx,
            plate_idx,
            e,
        )
