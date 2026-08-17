FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Pillow and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and seed data
COPY . .

# Ensure storage directory exists
RUN mkdir -p /app/storage/uploads /app/storage/catalog

ENV PYTHONPATH=/app
ENV STORAGE_LOCAL_DIR=/app/storage
ENV ENVIRONMENT=production

EXPOSE 8000

# Entrypoint script that initializes DB, seeds data if needed, and starts uvicorn
CMD ["sh", "-c", "python -m backend.seed_data.seed && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
