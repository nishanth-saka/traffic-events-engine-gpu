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
