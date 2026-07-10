FROM python:3.12-slim

WORKDIR /app

# gcc required by some C-extension packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies before copying app code (layer cache)
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy only the runtime directories
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY Models/ ./Models/
COPY alembic.ini .
COPY reset_test_data.py .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OUTPUT_DIR=/tmp/bills

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
