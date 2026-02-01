# app/ingest/frame/pipeline.py
import logging

from app.ingest.frame.types import Vehicle
from app.ingest.frame.plate_proposal import propose_plate_regions
from app.ingest.frame.logger import (
    log_pipeline_start,
    log_plate_summary,
    log_plate_candidates,
)

logger = logging.getLogger(__name__)


def run_frame_pipeline(*, camera_id, frame_ts, frame, vehicles):
    """
    Gate-2 frame pipeline.
    Vehicle → Plate proposals → Metrics + logs
    """

    log_pipeline_start(camera_id, len(vehicles))

    for idx, v in enumerate(vehicles):
        vehicle = Vehicle.from_detection(v, frame)
        
        # plates = propose_plate_regions(vehicle.crop)
        
        from app.ingest.frame.policy import CALIBRATION_PLATE_POLICY
        plates = propose_plate_regions(
            vehicle.crop,
            policy=CALIBRATION_PLATE_POLICY,
        )


        log_plate_summary(camera_id, idx, len(plates))
        log_plate_candidates(camera_id, idx, plates)

    return {
        "vehicles": vehicles,
        "plates": [],
    }
