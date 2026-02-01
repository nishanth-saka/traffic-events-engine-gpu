# app/ingest/frame/plate_proposal.py

import cv2
import numpy as np
from typing import List, Dict


def propose_plate_regions(vehicle_crop: np.ndarray) -> List[Dict]:
    """
    Gate-2: Plate proposal (CALIBRATION MODE – HIGH RECALL)

    Returns a list of candidate plate regions with metadata.
    Does NOT guarantee correctness – OCR will decide later.
    """

    if vehicle_crop is None:
        return []

    h, w = vehicle_crop.shape[:2]

    # Vehicle too small → impossible plate
    if h < 40 or w < 80:
        return []

    vehicle_area = h * w

    # -------------------------------------------------
    # Pre-processing
    # -------------------------------------------------
    gray = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(gray, 80, 160)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)

    # -------------------------------------------------
    # Contour detection
    # -------------------------------------------------
    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    candidates: List[Dict] = []

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)

        if cw < 20 or ch < 10:
            continue

        area = cw * ch
        area_ratio = area / float(vehicle_area)

        # -------------------------------------------------
        # 🔧 Gate-2 loosened thresholds (CALIBRATION)
        # -------------------------------------------------

        # Plate area: allow small plates
        if area_ratio < 0.008 or area_ratio > 0.20:
            continue

        aspect_ratio = cw / float(ch)

        # Indian plates + perspective skew
        if aspect_ratio < 1.8 or aspect_ratio > 6.0:
            continue

        # Edge density (blur tolerant)
        roi_edges = edges[y:y + ch, x:x + cw]
        edge_pixels = np.count_nonzero(roi_edges)
        edge_density = edge_pixels / float(area)

        if edge_density < 0.05:
            continue

        # Brightness sanity (soft gate)
        roi_gray = gray[y:y + ch, x:x + cw]
        mean_intensity = float(np.mean(roi_gray))

        if mean_intensity < 35 or mean_intensity > 235:
            continue

        # -------------------------------------------------
        # Candidate accepted
        # -------------------------------------------------
        candidates.append(
            {
                "bbox": (x, y, cw, ch),
                "area_ratio": round(area_ratio, 4),
                "aspect_ratio": round(aspect_ratio, 2),
                "edge_density": round(edge_density, 3),
                "mean_intensity": round(mean_intensity, 1),
            }
        )

    # Prefer plate-like shapes (wider first)
    candidates.sort(key=lambda c: c["aspect_ratio"], reverse=True)

    # Hard cap – avoid OCR explosion
    return candidates[:3]
