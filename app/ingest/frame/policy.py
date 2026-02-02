# app/ingest/frame/policy.py

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PlateProposalPolicy:
    # --- Geometry ---
    min_area_ratio: float
    max_area_ratio: float
    aspect_ratio_range: Tuple[float, float]

    # --- Spatial priors (normalized 0–1) ---
    min_cy: float              # vertical lower bound
    max_cx_offset: float       # |cx - 0.5| allowed

    # --- Hard exclusions ---
    top_exclusion_y: float     # anything above this is rejected


# -------------------------
# INDIA-SPECIFIC POLICIES
# -------------------------

CAR_PLATE_POLICY = PlateProposalPolicy(
    min_area_ratio=0.008,
    max_area_ratio=0.060,
    aspect_ratio_range=(3.8, 5.2),
    min_cy=0.55,
    max_cx_offset=0.25,
    top_exclusion_y=0.35,
)

AUTO_PLATE_POLICY = PlateProposalPolicy(
    min_area_ratio=0.010,
    max_area_ratio=0.080,
    aspect_ratio_range=(3.0, 4.5),
    min_cy=0.60,
    max_cx_offset=0.40,
    top_exclusion_y=0.40,
)

TRUCK_PLATE_POLICY = PlateProposalPolicy(
    min_area_ratio=0.015,
    max_area_ratio=0.120,
    aspect_ratio_range=(3.0, 6.0),
    min_cy=0.45,
    max_cx_offset=0.45,
    top_exclusion_y=0.30,
)

DEFAULT_PLATE_POLICY = CAR_PLATE_POLICY
