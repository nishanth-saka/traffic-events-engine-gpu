# app/ingest/frame/debug_dump.py

import os
import time
import cv2
import json
import logging

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
    bbox,
    plate_metrics: dict,
    ocr_result,
    decision: str,
):
    """
    Dump ONE OCR-correlated plate debug image + sidecar metadata (throttled).
    """

    if vehicle_crop is None or plate_crop is None or bbox is None:
        return

    now = time.time()
    last_ts = _last_dump_ts.get(cam_id, 0.0)

    if now - last_ts < DUMP_INTERVAL_SEC:
        return

    try:
        os.makedirs(DUMP_DIR, exist_ok=True)

        # -----------------------------
        # Visual debug image
        # -----------------------------
        vis = vehicle_crop.copy()
        x, y, w, h = bbox
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

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
            f"ts={int(frame_ts)}"
        )

        img_path = os.path.join(DUMP_DIR, f"{fname}.jpg")
        meta_path = os.path.join(DUMP_DIR, f"{fname}.json")

        cv2.imwrite(img_path, combined)

        # -----------------------------
        # Sidecar metadata
        # -----------------------------
        meta = {
            "camera_id": cam_id,
            "vehicle_idx": vehicle_idx,
            "plate_idx": plate_idx,
            "timestamp": int(frame_ts),
            "bbox": bbox,
            "plate_metrics": plate_metrics,
            "ocr": {
                "engine": getattr(ocr_result, "engine", None),
                "text": getattr(ocr_result, "text", ""),
                "confidence": getattr(ocr_result, "confidence", 0.0),
            },
            "decision": decision,
        }

        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        _last_dump_ts[cam_id] = now

        logger.warning(
            "[PLATE_DUMP] cam=%s vehicle=%d plate=%d decision=%s path=%s",
            cam_id,
            vehicle_idx,
            plate_idx,
            decision,
            img_path,
        )

    except Exception as e:
        logger.error(
            "[PLATE_DUMP] failed cam=%s vehicle=%d plate=%d err=%s",
            cam_id,
            vehicle_idx,
            plate_idx,
            e,
        )
