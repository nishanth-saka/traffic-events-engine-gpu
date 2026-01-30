FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (minimal, no X11)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install torch CPU wheels explicitly
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.0+cpu torchvision==0.16.0+cpu

# Install remaining deps
RUN pip install --no-cache-dir -r requirements.txt

# Hard guarantee: no GUI OpenCV
RUN pip uninstall -y opencv-python opencv-contrib-python || true

COPY . .

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
