from app.events.schema import TrafficEvent
from datetime import datetime
import uuid


def emit_event(event_type, camera_id, confidence, bbox=None, meta=None):
    return TrafficEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        camera_id=camera_id,
        timestamp=datetime.utcnow(),
        confidence=confidence,
        bbox=bbox,
        metadata=meta or {},
    )
