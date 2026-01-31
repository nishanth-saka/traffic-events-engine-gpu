FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 🔥 Torch safety (keep this)
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    libstdc++6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 🔥 COPY requirements FIRST (cache key)
COPY requirements.txt .

# 🔥 FORCE pip to show what it installs
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy app code AFTER deps
COPY . .

CMD ["python", "-m", "app.main"]
