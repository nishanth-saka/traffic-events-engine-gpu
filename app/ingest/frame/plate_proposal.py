# app/ingest/frame/plate_proposal.py

import cv2
import numpy as np
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def propose_plate_regions(vehicle_crop: np.ndarray) -> List[Dict]:
    """
    Propose license plate candidate regions from a vehicle crop.

    Returns a list of dicts with geometry + quality metrics.
    NO OCR. NO side effects.
    """

    if vehicle_crop is None:
        return []

    h, w = vehicle_crop.shape[:2]
    if h < 40 or w < 80:
        return []

    gray = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2GRAY)

    # Edge detection
    edges = cv2.Canny(gray, 100, 200)

    # Morphological close to connect characters
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    candidates = []

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)

        aspect = cw / float(ch)
        area = cw * ch
        area_ratio = area / float(w * h)

        # Plate geometry heuristics
        if not (2.0 <= aspect <= 6.0):
            continue
        if not (0.01 <= area_ratio <= 0.2):
            continue

        crop = vehicle_crop[y:y + ch, x:x + cw]

        blur = _blur_score(crop)
        skew = _skew_angle(cnt)

        candidates.append({
            "bbox": [x, y, x + cw, y + ch],
            "area_ratio": round(area_ratio, 4),
            "aspect": round(aspect, 2),
            "blur": round(blur, 1),
            "skew": round(skew, 1),
        })

    return candidates


def _blur_score(img: np.ndarray) -> float:
    """Variance of Laplacian (higher = sharper)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def _skew_angle(cnt) -> float:
    """Absolute angle of minimum-area rectangle."""
    rect = cv2.minAreaRect(cnt)
    angle = rect[-1]
    if angle < -45:
        angle = 90 + angle
    return abs(angle)
