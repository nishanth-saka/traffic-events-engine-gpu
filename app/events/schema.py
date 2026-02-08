from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class TrafficEvent(BaseModel):
    event_id: str
    event_type: str           # wrong_direction, count, congestion
    camera_id: str
    timestamp: datetime
    confidence: float

    bbox: Optional[BoundingBox] = None
    snapshot_ref: Optional[str] = None
    metadata: dict = {}
