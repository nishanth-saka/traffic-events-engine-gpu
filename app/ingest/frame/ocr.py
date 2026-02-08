python3 - <<'EOF'

# TRAFFIC/app/ingest/frame/ocr.py

import time
import numpy as np
import cv2
from paddleocr import PaddleOCR

print("Initializing PaddleOCR (GPU)...")
ocr = PaddleOCR(
    use_angle_cls=True,
    lang="en",
    use_gpu=True,
    show_log=False,
)

# 🔥 Warmup (critical)
dummy = np.zeros((64, 256, 3), dtype=np.uint8)
ocr.ocr(dummy, cls=True)

# Test image
img = np.zeros((120, 320, 3), dtype=np.uint8)
cv2.putText(
    img, "TS09AB1234",
    (5, 80),
    cv2.FONT_HERSHEY_SIMPLEX,
    1.6, (255, 255, 255), 3
)

t0 = time.time()
res = ocr.ocr(img, cls=True)
lat = (time.time() - t0) * 1000

print("OCR result:", res)
print(f"Latency: {lat:.1f} ms")
EOF
