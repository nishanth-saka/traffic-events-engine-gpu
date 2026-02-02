FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 🔥 Torch safety (keep this)
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1

WORKDIR /app

# -------------------------------------------------
# System deps (OCR + OpenCV)
# -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    libstdc++6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# Python deps
# -------------------------------------------------
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------
# App code
# -------------------------------------------------
COPY . .

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
