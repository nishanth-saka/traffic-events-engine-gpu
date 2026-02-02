# app/ingest/frame/plate_proposal.py

import cv2
import numpy as np
from typing import List, Dict

from app.ingest.frame.policy import (
    PlateProposalPolicy,
    CAR_PLATE_POLICY,
    AUTO_PLATE_POLICY,
    TRUCK_PLATE_POLICY,
    DEFAULT_PLATE_POLICY,
)


def _estimate_blur(gray: np.ndarray) -> float:
    """Cheap sharpness metric (variance of Laplacian)."""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def propose_plate_regions(
    vehicle_crop: np.ndarray,
    *,
    vehicle_type: str | None = None,
    policy: PlateProposalPolicy | None = None,
) -> List[Dict]:
    """
    Gate-2: Propose license plate candidate regions.

    Includes:
    - Vehicle-type spatial priors (India-specific)
    - Hard top-of-vehicle exclusion
    - Tightened aspect ratio bands
    """

    if vehicle_crop is None:
        return []

    h, w = vehicle_crop.shape[:2]
    if h < 40 or w < 80:
        return []

    # -----------------------------
    # Policy selection
    # -----------------------------
    if policy is None:
        if vehicle_type in {"auto", "autorickshaw"}:
            policy = AUTO_PLATE_POLICY
        elif vehicle_type in {"truck", "bus"}:
            policy = TRUCK_PLATE_POLICY
        else:
            policy = DEFAULT_PLATE_POLICY

    # Defensive fallback (future-proof)
    if policy is None:
        policy = DEFAULT_PLATE_POLICY

    gray = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    candidates: List[Dict] = []
    vehicle_area = float(h * w)

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        if cw <= 0 or ch <= 0:
            continue

        # 🔹 Noise guard: ultra-thin contours
        if ch < 12 or cw < 40:
            continue

        area_ratio = (cw * ch) / vehicle_area
        if not (policy.min_area_ratio <= area_ratio <= policy.max_area_ratio):
            continue

        aspect = cw / float(ch)
        if not (policy.aspect_ratio_range[0] <= aspect <= policy.aspect_ratio_range[1]):
            continue

        # -----------------------------
        # Normalized spatial checks
        # -----------------------------
        cx = (x + cw / 2) / w
        cy = (y + ch / 2) / h

        # 🔴 Hard top exclusion (roof / canopy / rails)
        if y < policy.top_exclusion_y * h:
            continue

        # 🔴 Vertical placement prior
        if cy < policy.min_cy:
            continue

        # 🔴 Horizontal centering prior
        if abs(cx - 0.5) > policy.max_cx_offset:
            continue

        plate_crop = gray[y:y + ch, x:x + cw]
        blur = _estimate_blur(plate_crop)

        candidates.append({
            "bbox": (x, y, cw, ch),
            "area_ratio": round(area_ratio, 4),
            "aspect": round(aspect, 2),
            "cx": round(cx, 3),
            "cy": round(cy, 3),
            "blur": round(blur, 1),
        })

    return candidates
