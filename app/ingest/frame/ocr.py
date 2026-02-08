# TRAFFIC/app/ingest/frame/ocr.py

from dataclasses import dataclass
import logging
import re
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# -------------------------------------------------
# OCR Result model
# -------------------------------------------------
@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str


# -------------------------------------------------
# Normalization helpers (lightweight)
# -------------------------------------------------
CHAR_NORMALIZE_MAP = {
    "O": "0",
    "I": "1",
    "Z": "2",
    "S": "5",
    "B": "8",
    "G": "6",
}


def normalize_text(text: str) -> str:
    return "".join(CHAR_NORMALIZE_MAP.get(c, c) for c in text.upper())


# -------------------------------------------------
# PaddleOCR singleton
# -------------------------------------------------
_PADDLE_OCR = None


def get_paddle_ocr():
    global _PADDLE_OCR
    if _PADDLE_OCR is not None:
        return _PADDLE_OCR

    try:
        from paddleocr import PaddleOCR

        logger.info("[OCR] Initializing PaddleOCR (GPU if available)")
        _PADDLE_OCR = PaddleOCR(
            use_angle_cls=False,
            lang="en",
            use_gpu=True,          # GPU if present
            show_log=False,
        )
        return _PADDLE_OCR

    except Exception as e:
        logger.warning("[OCR] PaddleOCR init failed: %s", e)
        _PADDLE_OCR = False
        return None


# -------------------------------------------------
# OCR runner (GPU-first, CPU-safe)
# -------------------------------------------------
def run_ocr(plate_img, *, mode: str = "light") -> OCRResult:
    """
    Step-4 OCR:
    - PaddleOCR (GPU-first)
    - No early rejection
    - Always returns best-effort text
    """

    if plate_img is None or plate_img.size == 0:
        return OCRResult("", 0.0, "none")

    # ---------------------------------
    # Preprocessing (light, OCR-friendly)
    # ---------------------------------
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)

    # Upscale aggressively — helps Paddle a LOT
    gray = cv2.resize(
        gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC
    )

    # mild contrast normalization
    gray = cv2.equalizeHist(gray)

    # Paddle expects RGB
    rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    # ---------------------------------
    # PaddleOCR
    # ---------------------------------
    ocr_engine = get_paddle_ocr()
    if not ocr_engine:
        return OCRResult("", 0.0, "paddle_unavailable")

    try:
        results = ocr_engine.ocr(rgb, cls=False)
    except Exception as e:
        logger.exception("[OCR] PaddleOCR failure: %s", e)
        return OCRResult("", 0.0, "paddle_error")

    texts = []
    confs = []

    for line in results or []:
        try:
            text, conf = line[1]
            clean = re.sub(r"[^A-Z0-9]", "", text.upper())
            if not clean:
                continue

            normalized = normalize_text(clean)
            texts.append(normalized)
            confs.append(float(conf))
        except Exception:
            continue

    if not texts:
        return OCRResult("", 0.0, "paddle")

    text = "".join(texts)

    confidence = 0.0
    if confs:
        confidence = sum(confs) / len(confs)

    logger.info(
        "[OCR] engine=paddle text=%r conf=%.3f",
        text,
        confidence,
    )

    return OCRResult(text, confidence, "paddle")
