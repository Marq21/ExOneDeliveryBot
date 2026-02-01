
FROM python:3.10-slim

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgl1 \
    libglib2.0-0 \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Добавляем /app в PYTHONPATH
ENV PYTHONPATH=/app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ ./src/
COPY static/ ./static/

# Создаём пользователя
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Запускаем бота
CMD ["python", "src/main.py"]