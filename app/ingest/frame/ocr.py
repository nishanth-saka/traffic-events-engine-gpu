from dataclasses import dataclass


@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str = "stub"


def run_ocr(plate_img, *, mode: str = "light") -> OCRResult:
    """
    OCR runner.
    mode = light | heavy
    """

    # 🔧 stub for now
    return OCRResult(
        text="KA01AB1234",
        confidence=0.85,
        engine="stub",
    )
