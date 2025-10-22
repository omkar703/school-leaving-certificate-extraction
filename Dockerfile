# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System dependencies for OCR and image/PDF handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Install Python deps if present; otherwise install common OCR libs
RUN bash -lc 'if [ -f requirements.txt ]; then pip install -r requirements.txt; else pip install pytesseract pillow opencv-python-headless pdf2image; fi'

# Ensure start script is executable
RUN chmod +x /app/start.sh || true

ENTRYPOINT ["/app/start.sh"]
