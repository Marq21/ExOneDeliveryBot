# Dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgl1-mesa-glx \
    libglib2.0-0 \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ТОЛЬКО исходники
COPY src/ ./src/
COPY static/ ./static/

# Безопасность
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

CMD ["python", "src/main.py"]