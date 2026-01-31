FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.0+cpu torchvision==0.16.0+cpu

RUN pip install --no-cache-dir -r requirements.txt

RUN pip uninstall -y opencv-python opencv-contrib-python || true

COPY . .

CMD ["python", "-m", "app.main"]
