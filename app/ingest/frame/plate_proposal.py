# app/ingest/frame/plate_proposal.py

import cv2
import numpy as np
from typing import List, Dict

from app.ingest.frame.policy import DEFAULT_PLATE_POLICY, PlateProposalPolicy


def propose_plate_regions(
    vehicle_crop: np.ndarray,
    policy: PlateProposalPolicy = DEFAULT_PLATE_POLICY,
) -> List[Dict]:
    """
    Propose license plate candidate regions from a vehicle crop.

    Gate-2 behavior:
    - Geometry & size are gated by policy
    - Blur & skew are COMPUTED, not filtered (metrics only)

    Returns:
        List of dicts with bbox + quality metrics
    """

    if vehicle_crop is None:
        return []

    h, w = vehicle_crop.shape[:2]
    if h < 40 or w < 80:
        return []

    gray = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    candidates: List[Dict] = []

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)

        # --- Absolute size guardrails ---
        if cw < policy.min_width or ch < policy.min_height:
            continue

        aspect = cw / float(ch)
        area_ratio = (cw * ch) / float(w * h)

        # --- Geometry constraints ---
        if not (policy.min_aspect <= aspect <= policy.max_aspect):
            continue
        if not (policy.min_area_ratio <= area_ratio <= policy.max_area_ratio):
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


# -------------------------------------------------
# Metrics helpers
# -------------------------------------------------

def _blur_score(img: np.ndarray) -> float:
    """Variance of Laplacian (higher = sharper)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def _skew_angle(cnt) -> float:
    """Absolute skew angle from minimum-area rectangle."""
    rect = cv2.minAreaRect(cnt)
    angle = rect[-1]
    if angle < -45:
        angle = 90 + angle
    return abs(angle)
