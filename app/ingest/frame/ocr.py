# app/ingest/frame/ocr.py

from dataclasses import dataclass
import cv2
import pytesseract
print("✅ Tesseract:", pytesseract.get_tesseract_version(), flush=True)
import re


@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str


def run_ocr(plate_img, *, mode: str = "light") -> OCRResult:
    """
    Lightweight local OCR using Tesseract.
    No billing. No network. Calibration-friendly.
    """

    if plate_img is None or plate_img.size == 0:
        return OCRResult("", 0.0, "tesseract")

    # ----------------------------
    # Preprocessing (very mild)
    # ----------------------------
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(
        gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC
    )

    # ----------------------------
    # OCR
    # ----------------------------
    data = pytesseract.image_to_data(
        gray,
        output_type=pytesseract.Output.DICT,
        config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    )

    texts = []
    confs = []

    for txt, conf in zip(data["text"], data["conf"]):
        if conf != "-1" and txt.strip():
            clean = re.sub(r"[^A-Z0-9]", "", txt.upper())
            if clean:
                texts.append(clean)
                confs.append(float(conf))

    if not texts:
        return OCRResult("", 0.0, "tesseract")

    text = "".join(texts)
    confidence = sum(confs) / (len(confs) * 100.0)

    return OCRResult(text, confidence, "tesseract")
