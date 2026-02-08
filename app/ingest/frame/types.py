# app/ingest/frame/types.py
from dataclasses import dataclass
import numpy as np


@dataclass
class Vehicle:
    bbox: tuple
    confidence: float
    cls: str
    crop: np.ndarray

    @staticmethod
    def from_detection(det: dict, frame: np.ndarray) -> "Vehicle":
        x1, y1, x2, y2 = det["bbox"]
        crop = frame[y1:y2, x1:x2]

        return Vehicle(
            bbox=det["bbox"],
            confidence=det["confidence"],
            cls=det["class"],
            crop=crop,
        )
