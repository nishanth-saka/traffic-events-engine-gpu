# app/ingest/frame/pipeline.py

import logging

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
    ENABLE_HEAVY_OCR,
)

logger = logging.getLogger(__name__)


def run_frame_pipeline(*, camera_id, frame_ts, frame, vehicles):
    """
    Gate-2 frame pipeline with OCR debug metadata.
    """

    log_pipeline_start(camera_id, len(vehicles))

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

        for p_idx, plate in enumerate(plates):
            try:
                # -------------------------
                # Cheap gate
                # -------------------------
                if not cheap_plate_gate(plate):
                    logger.info(
                        "[PLATE-GATE] reject | cam=%s vehicle=%d plate=%d",
                        camera_id,
                        v_idx,
                        p_idx,
                    )
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

                # -------------------------
                # Decision
                # -------------------------
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

                elif ocr.confidence >= CANDIDATE_CONF_THRESHOLD:
                    decision = "candidate"
                    emit_event(
                        "plate.candidate",
                        camera_id=camera_id,
                        vehicle_idx=v_idx,
                        plate_idx=p_idx,
                        plate=ocr.text,
                        confidence=ocr.confidence,
                    )
                else:
                    decision = "rejected"

                # -------------------------
                # Debug dump + metadata
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
