# app/events/engine.py

import time
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class EventsEngine:
    """
    EventsEngine

    Responsibility:
    - Consume latest detections per camera
    - Apply minimal domain logic
    - Emit semantic traffic events

    NOTE:
    - This engine is stateless by design (Phase 4)
    - Temporal correlation / tracking comes later
    """

    def __init__(self, detection_manager):
        self.detection_manager = detection_manager

    def process_camera(self, cam_id: str) -> List[Dict]:
        """
        Process one camera's detections and emit events.

        Returns:
            List of event dicts
        """

        # -------------------------------------------------
        # Step 4: consume detections
        # -------------------------------------------------
        detections = self.detection_manager.get(cam_id)

        logger.info(
            "[TRACE][%s] Event engine received %d detections",
            cam_id,
            len(detections),
        )

        events: List[Dict] = []

        # -------------------------------------------------
        # Step 5: emit events
        # -------------------------------------------------
        for d in detections:
            event = {
                "type": "vehicle_detected",
                "cam_id": cam_id,
                "class": d["class"],
                "confidence": d["confidence"],
                "bbox": d["bbox"],
                "ts": time.time(),
            }

            events.append(event)

            logger.info(
                "[TRACE][%s] Event emitted: %s",
                cam_id,
                event["type"],
            )

        return events
