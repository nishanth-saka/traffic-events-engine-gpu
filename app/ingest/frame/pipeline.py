# TRAFFIC/app/ingest/frame/pipeline.py

import logging
import time
from collections import Counter, defaultdict

from app.ingest.frame.types import Vehicle
from app.ingest.frame.plate_proposal import propose_plate_regions
from app.ingest.frame.logger import (
    log_pipeline_start,
    log_plate_summary,
    log_plate_candidates,
)
from app.ingest.frame.ocr import run_ocr
from app.ingest.frame.quality_gate import cheap_plate_gate
from app.ingest.frame.debug_dump import maybe_dump_plate_crop
from app.ingest.frame.events import emit_event
from app.ingest.frame.policy import (
    CALIBRATION_PLATE_POLICY,
    CANDIDATE_CONF_THRESHOLD,
    CONFIRMED_CONF_THRESHOLD,
)

logger = logging.getLogger(__name__)

# -------------------------------------------------
# 🔑 Simple temporal OCR memory (per vehicle)
# -------------------------------------------------
# key = (camera_id, vehicle_idx)
# value = list of (timestamp, text, confidence)
_OCR_HISTORY = defaultdict(list)

# how long we remember OCR (seconds)
OCR_MEMORY_TTL = 3.0

# how many votes needed to emit candidate
MIN_VOTES_FOR_CANDIDATE = 2


def _has_digit(text: str) -> bool:
    return any(c.isdigit() for c in text)


def _cleanup_history(now):
    for k, items in list(_OCR_HISTORY.items()):
        _OCR_HISTORY[k] = [
            (ts, t, c) for (ts, t, c) in items if now - ts <= OCR_MEMORY_TTL
        ]
        if not _OCR_HISTORY[k]:
            del _OCR_HISTORY[k]


def _aggregate_text(key):
    """
    Vote across recent OCR outputs.
    Prefer digit-containing strings.
    """
    items = _OCR_HISTORY.get(key, [])
    if not items:
        return None, 0

    texts = [t for _, t, _ in items if t]
    if not texts:
        return None, 0

    # weight: digit-bearing strings count more
    weighted = []
    for t in texts:
        weight = 2 if _has_digit(t) else 1
        weighted.extend([t] * weight)

    counter = Counter(weighted)
    best, votes = counter.most_common(1)[0]
    return best, votes


def run_frame_pipeline(*, camera_id, frame_ts, frame, vehicles):
    """
    Gate-2 frame pipeline with temporal OCR aggregation.
    """

    log_pipeline_start(camera_id, len(vehicles))
    now = time.time()
    _cleanup_history(now)

    for v_idx, v in enumerate(vehicles):
        vehicle = Vehicle.from_detection(v, frame)

        if vehicle.crop is None:
            continue

        h, w = vehicle.crop.shape[:2]
        if h < 40 or w < 80:
            continue

        plates = propose_plate_regions(
            vehicle.crop,
            policy=CALIBRATION_PLATE_POLICY,
        )

        log_plate_summary(camera_id, v_idx, len(plates))
        log_plate_candidates(camera_id, v_idx, plates)

        key = (camera_id, v_idx)

        for p_idx, plate in enumerate(plates):
            try:
                # -------------------------
                # Cheap gate
                # -------------------------
                if not cheap_plate_gate(plate):
                    continue

                # -------------------------
                # OCR
                # -------------------------
                ocr = run_ocr(plate["crop"], mode="light")

                logger.info(
                    "[OCR] cam=%s vehicle=%d plate=%d text=%r conf=%.3f",
                    camera_id,
                    v_idx,
                    p_idx,
                    ocr.text,
                    ocr.confidence,
                )

                # store OCR result (even weak)
                if ocr.text:
                    _OCR_HISTORY[key].append(
                        (now, ocr.text, ocr.confidence)
                    )

                agg_text, votes = _aggregate_text(key)

                decision = "rejected"

                # -------------------------
                # Decision (temporal)
                # -------------------------
                if agg_text and votes >= MIN_VOTES_FOR_CANDIDATE:
                    decision = "candidate"
                    emit_event(
                        "plate.candidate",
                        camera_id=camera_id,
                        vehicle_idx=v_idx,
                        plate_idx=p_idx,
                        plate=agg_text,
                        confidence=votes / 5.0,  # pseudo-confidence
                    )

                if ocr.confidence >= CONFIRMED_CONF_THRESHOLD:
                    decision = "confirmed"
                    emit_event(
                        "plate.confirmed",
                        camera_id=camera_id,
                        vehicle_idx=v_idx,
                        plate_idx=p_idx,
                        plate=ocr.text,
                        confidence=ocr.confidence,
                    )

                # -------------------------
                # Debug dump
                # -------------------------
                maybe_dump_plate_crop(
                    cam_id=camera_id,
                    frame_ts=frame_ts,
                    vehicle_idx=v_idx,
                    plate_idx=p_idx,
                    vehicle_crop=vehicle.crop,
                    plate_crop=plate["crop"],
                    bbox=plate.get("bbox"),
                    plate_metrics={
                        "area_ratio": plate["area_ratio"],
                        "aspect": plate["aspect"],
                        "blur": plate["blur"],
                        "skew": plate["skew"],
                    },
                    ocr_result=ocr,
                    decision=decision,
                )

            except Exception as e:
                logger.exception(
                    "[OCR] failure | cam=%s vehicle=%d plate=%d err=%s",
                    camera_id,
                    v_idx,
                    p_idx,
                    e,
                )

    return {"vehicles": vehicles, "plates": []}
