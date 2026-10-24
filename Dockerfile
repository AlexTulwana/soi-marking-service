FROM python:3.10-slim

# Tesseract is the OCR program that pytesseract calls
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

# Install packages first, so this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Run as a normal user, not root
RUN useradd --create-home appuser
USER appuser

EXPOSE 8001

# Settings (API key, Gemini key, etc.) are passed in as environment variables
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
