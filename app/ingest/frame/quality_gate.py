import cv2
import numpy as np
from dataclasses import dataclass

logging.getLogger(__name__).info("cv2 loaded from: %s", cv2.__file__)

@dataclass
class GateResult:
    passed: bool
    reason: str
    score: float


def evaluate_plate_quality(plate_img) -> GateResult:
    h, w = plate_img.shape[:2]
    area = h * w

    if area < 2000:
        return GateResult(False, "too_small", area)

    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F).var()

    if lap < 100:
        return GateResult(False, "blur", lap)

    return GateResult(True, "ok", lap)
