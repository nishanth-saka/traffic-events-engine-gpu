# app/ingest/frame/plate_proposal.py

import os
import cv2
import numpy as np
from typing import List, Dict, Optional

# ------------------------------------
# Internal debug switch (SAFE)
# ------------------------------------
DEBUG_INTERNAL_PLATES = os.getenv("DEBUG_INTERNAL_PLATES", "0") == "1"
DEBUG_DIR = "/tmp/plate_debug"


def _estimate_blur(gray: np.ndarray) -> float:
    """Variance of Laplacian (cheap + standard)."""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _estimate_skew(_: np.ndarray) -> float:
    """Placeholder (real skew later via Hough / PCA)."""
    return 0.0


def propose_plate_regions(
    vehicle_crop: np.ndarray,
    *,
    policy: Optional[str] = None,
) -> List[Dict]:
    """
    Generate candidate license plate regions from a VEHICLE CROP.

    ⚠️ IMPORTANT:
    - All returned bboxes are RELATIVE TO vehicle_crop
    - No resizing is performed in this function
    - Any downstream drawing MUST respect this coordinate space

    Calibration mode:
    - Loose thresholds
    - Metrics computed, NOT filtered
    """

    if vehicle_crop is None:
        return []

    if vehicle_crop.ndim != 3:
        return []

    h, w = vehicle_crop.shape[:2]

    # Calibration: avoid aggressive early exits
    if h < 30 or w < 60:
        return []

    # Defensive copy (prevents accidental mutation upstream)
    vehicle_crop = vehicle_crop.copy()

    gray = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2GRAY)

    # -----------------------------
    # Policy thresholds
    # -----------------------------
    if policy == "calibration":
        canny_low, canny_high = 50, 150
        min_area_ratio = 0.0015
        aspect_min, aspect_max = 1.8, 7.5
    else:
        canny_low, canny_high = 100, 200
        min_area_ratio = 0.005
        aspect_min, aspect_max = 2.2, 6.0

    edges = cv2.Canny(gray, canny_low, canny_high)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    proposals: List[Dict] = []
    img_area = float(h * w)

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)

        # Absolute sanity
        if cw <= 0 or ch <= 0:
            continue

        area = float(cw * ch)
        area_ratio = area / img_area

        if area_ratio < min_area_ratio:
            continue

        aspect = cw / max(ch, 1)
        if not (aspect_min < aspect < aspect_max):
            continue

        # Clamp to image bounds (paranoia)
        x2 = min(x + cw, w)
        y2 = min(y + ch, h)
        crop = vehicle_crop[y:y2, x:x2]

        if crop.size == 0:
            continue

        crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        proposal = {
            "bbox": (x, y, x2 - x, y2 - y),  # RELATIVE TO vehicle_crop
            "crop": crop,
            "area": area,
            "area_ratio": area_ratio,
            "aspect": aspect,
            "blur": _estimate_blur(crop_gray),
            "skew": _estimate_skew(crop_gray),
        }

        proposals.append(proposal)

        # ------------------------------------
        # 🔍 INTERNAL DEBUG (SOURCE OF TRUTH)
        # ------------------------------------
        if DEBUG_INTERNAL_PLATES:
            os.makedirs(DEBUG_DIR, exist_ok=True)
            dbg = vehicle_crop.copy()
            cv2.rectangle(
                dbg,
                (x, y),
                (x2, y2),
                (0, 0, 255),  # RED = internal truth
                2,
            )
            cv2.imwrite(
                f"{DEBUG_DIR}/_internal_plate_{x}_{y}_{cw}_{ch}.jpg",
                dbg,
            )

    # -----------------------------
    # Ranking (NOT filtering)
    # Bigger + better aspect first
    # -----------------------------
    proposals.sort(
        key=lambda p: (p["area_ratio"], p["aspect"]),
        reverse=True,
    )

    return proposals
