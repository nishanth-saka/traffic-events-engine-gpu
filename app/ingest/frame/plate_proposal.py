# app/ingest/frame/plate_proposal.py

import cv2
import numpy as np
from typing import List, Dict, Optional


def propose_plate_regions(
    vehicle_crop: np.ndarray,
    *,
    policy: Optional[str] = None,
) -> List[Dict]:
    """
    Generate candidate license plate regions from a vehicle crop.

    policy:
        None / "default"  → conservative heuristics
        "calibration"     → looser thresholds (Gate-2 tuning mode)
    """

    if vehicle_crop is None:
        return []

    h, w = vehicle_crop.shape[:2]
    if h < 40 or w < 80:
        return []

    gray = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2GRAY)

    # 🔓 Loosen thresholds in calibration mode
    if policy == "calibration":
        canny_low, canny_high = 50, 150
        min_area_ratio = 0.002
    else:
        canny_low, canny_high = 100, 200
        min_area_ratio = 0.005

    edges = cv2.Canny(gray, canny_low, canny_high)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    proposals: List[Dict] = []
    img_area = h * w

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        area = cw * ch

        if area / img_area < min_area_ratio:
            continue

        aspect = cw / max(ch, 1)
        if 2.0 < aspect < 6.5:
            proposals.append(
                {
                    "bbox": (x, y, cw, ch),
                    "area": area,
                    "aspect": aspect,
                }
            )

    return proposals
