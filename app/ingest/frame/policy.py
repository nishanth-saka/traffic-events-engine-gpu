# TRAFFIC/app/ingest/frame/policy.py

from dataclasses import dataclass


@dataclass(frozen=True)
class PlateProposalPolicy:
    """
    Geometry & quality constraints for plate proposals.
    """

    # Geometry
    min_aspect: float = 2.0
    max_aspect: float = 6.0

    min_area_ratio: float = 0.01
    max_area_ratio: float = 0.20

    # Quality
    min_blur: float = 60.0
    max_skew: float = 20.0

    # Size
    min_width: int = 60
    min_height: int = 20


DEFAULT_PLATE_POLICY = PlateProposalPolicy()

# -------------------------------------------------
# Calibration / SUB-stream friendly policy
# -------------------------------------------------
CALIBRATION_PLATE_POLICY = PlateProposalPolicy(
    min_aspect=1.5,
    max_aspect=8.0,
    min_area_ratio=0.005,
    max_area_ratio=0.30,
    min_width=40,
    min_height=15,
    min_blur=0.0,
    max_skew=45.0,
)

# -------------------------------------------------
# OCR gating thresholds
# -------------------------------------------------

# candidate now comes from TEMPORAL votes, not raw confidence
CANDIDATE_CONF_THRESHOLD = 0.10   # effectively permissive

# confirmed stays strict
CONFIRMED_CONF_THRESHOLD = 0.75

# heavy OCR still off (later step)
ENABLE_HEAVY_OCR = False
