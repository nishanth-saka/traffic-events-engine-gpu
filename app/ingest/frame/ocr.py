# TRAFFIC/app/ingest/frame/ocr.py

from dataclasses import dataclass
import cv2
import pytesseract
import re
import logging

logger = logging.getLogger(__name__)


# -------------------------------
# OCR Result model
# -------------------------------
@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str


# -------------------------------
# Normalization helpers
# -------------------------------
CHAR_NORMALIZE_MAP = {
    "O": "0",
    "I": "1",
    "Z": "2",
    "S": "5",
    "B": "8",
    "G": "6",
}


def normalize_text(text: str) -> str:
    """
    Normalize common OCR confusions.
    This is intentionally LIGHT — no regex enforcement here.
    """
    return "".join(CHAR_NORMALIZE_MAP.get(c, c) for c in text.upper())


# -------------------------------
# OCR runner (Step-2: real OCR)
# -------------------------------
def run_ocr(plate_img, *, mode: str = "light") -> OCRResult:
    """
    Lightweight local OCR using Tesseract.

    Step-2 behavior:
    - OCR ALWAYS returns text if anything is detected
    - No hard rejection here
    - Weak / partial / numeric strings are allowed
    - Aggregation decides later
    """

    if plate_img is None or plate_img.size == 0:
        logger.debug("[OCR] empty plate image")
        return OCRResult("", 0.0, "tesseract")

    # ---------------------------------
    # Preprocessing
    # ---------------------------------
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)

    # Upscale small SUB-stream plates
    gray = cv2.resize(
        gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC
    )

    # Adaptive thresholding (robust for plates)
    gray = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2,
    )

    # ---------------------------------
    # OCR (Tesseract)
    # ---------------------------------
    data = pytesseract.image_to_data(
        gray,
        output_type=pytesseract.Output.DICT,
        config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    )

    texts = []
    confs = []

    for raw_txt, conf in zip(data["text"], data["conf"]):
        if conf == "-1":
            continue

        raw_txt = raw_txt.strip()
        if not raw_txt:
            continue

        clean = re.sub(r"[^A-Z0-9]", "", raw_txt.upper())
        if not clean:
            continue

        normalized = normalize_text(clean)

        texts.append(normalized)
        try:
            confs.append(float(conf))
        except Exception:
            confs.append(0.0)

    # ---------------------------------
    # Result assembly (NO rejection)
    # ---------------------------------
    if not texts:
        logger.debug("[OCR] no text detected")
        return OCRResult("", 0.0, "tesseract")

    text = "".join(texts)

    # Average confidence, normalized to 0–1
    confidence = 0.0
    if confs:
        confidence = sum(confs) / (len(confs) * 100.0)

    logger.info(
        "[OCR] engine=tesseract text='%s' conf=%.3f",
        text,
        confidence,
    )

    return OCRResult(text, confidence, "tesseract")
