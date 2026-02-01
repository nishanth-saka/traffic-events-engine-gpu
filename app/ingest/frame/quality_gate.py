import numpy as np
import logging
from dataclasses import dataclass
import cv2

logging.getLogger(__name__).info("cv2 loaded from: %s", cv2.__file__)

# -------------------------------------------------
# Gate-2 calibration toggle
# -------------------------------------------------
GATE2_CALIBRATION_MODE = True


@dataclass
class GateResult:
    passed: bool
    reason: str
    score: float


def evaluate_plate_quality(plate_img) -> GateResult:
    h, w = plate_img.shape[:2]
    area = h * w

    # -------------------------------------------------
    # Size gate (loosened in calibration)
    # -------------------------------------------------
    min_area = 2000
    if GATE2_CALIBRATION_MODE:
        min_area = 900

    if area < min_area:
        return GateResult(False, "too_small", area)

    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F).var()

    # -------------------------------------------------
    # Blur gate (loosened in calibration)
    # -------------------------------------------------
    min_lap = 100
    if GATE2_CALIBRATION_MODE:
        min_lap = 45

    if lap < min_lap:
        return GateResult(False, "blur", lap)

    return GateResult(True, "ok", lap)
