# app/ingest/frame/policy.py

from dataclasses import dataclass


@dataclass(frozen=True)
class PlateProposalPolicy:
    """
    Geometry & quality constraints for plate proposals.
    Tunable without touching algorithm code.
    """

    # Geometry
    min_aspect: float = 2.0
    max_aspect: float = 6.0

    min_area_ratio: float = 0.01
    max_area_ratio: float = 0.20

    # Quality
    min_blur: float = 60.0        # Laplacian variance
    max_skew: float = 20.0        # degrees

    # Size guardrails (absolute px)
    min_width: int = 60
    min_height: int = 20


# 🔒 Default global policy (Gate-2)
DEFAULT_PLATE_POLICY = PlateProposalPolicy()

# -------------------------------------------------
# Gate-2 CALIBRATION policy (SUB stream friendly)
# Intentionally loose — metrics, not filtering
# -------------------------------------------------

CALIBRATION_PLATE_POLICY = PlateProposalPolicy(
    # Geometry — looser
    min_aspect=1.5,
    max_aspect=8.0,

    min_area_ratio=0.005,
    max_area_ratio=0.30,

    # Size — SUB stream tolerant
    min_width=40,
    min_height=15,

    # Quality (NOT enforced yet, metrics only)
    min_blur=0.0,
    max_skew=45.0,
)

