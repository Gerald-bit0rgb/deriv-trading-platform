# ─────────────────────────────────────────────────────────────────────────────
# Multi-stage Dockerfile for the FastAPI backend
# ─────────────────────────────────────────────────────────────────────────────

# Stage 1: dependency builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools for native extensions (psycopg2, numpy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# Stage 2: final runtime image
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Runtime lib only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy application source
COPY backend/ .

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser && \
    mkdir -p logs && \
    chown -R appuser:appuser /app
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health-check so Render (and Docker) know the service is up
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
