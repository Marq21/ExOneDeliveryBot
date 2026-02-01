FROM python:3.10-slim

# Устанавливаем ВСЕ необходимые системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgl1 \
    libglib2.0-0 \
    zlib1g-dev \
    libzbar0 \          
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY static/ ./static/

RUN useradd --create-home --shell /bin/bash appuser
USER appuser

CMD ["python", "src/main.py"]