# syntax=docker/dockerfile:1.6
############################################################
# MG-ERP Authentication Service Dockerfile
# Multi-stage build for smaller final image
############################################################
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory at parent so package folder 'auth' is on PYTHONPATH
WORKDIR /app

# System deps (add build-essential if compiling wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install dependencies separately for better layer caching
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source into /app/auth to preserve package name
COPY . auth/

# Prepare writable logs directory and fix ownership for non-root user
RUN mkdir -p /app/logs \
  && chown -R appuser:appuser /app

# Expose service port (adjust if different)
EXPOSE 8004

# Environment variable defaults (override at runtime)
# SECURITY: Override SECRET_KEY in production via `docker run -e SECRET_KEY=...`
ENV AUTH_DATABASE_URL="postgresql+asyncpg://mguser:mgpassword@postgres/mgerp" \
    SECRET_KEY="change-me" \
    ACCESS_TOKEN_EXPIRE_MINUTES=30 \
    REFRESH_TOKEN_EXPIRE_DAYS=7 \
    DEBUG="false" \
    INVENTORY_SERVICE_URL="http://inventory:8002" \
    LEDGER_SERVICE_URL="http://ledger:8000" \
    POS_SERVICE_URL="http://pos:8001" \
    HOST="0.0.0.0" \
  PORT=8004 \
  LOG_DIR="/app/logs" \
  LOG_TO_STDOUT="true"

# Switch to non-root user
USER appuser

# Healthcheck (optional): simple GET to /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:8004/health || exit 1

# Default command: run with uvicorn using package path
CMD ["uvicorn", "auth.main:app", "--host", "0.0.0.0", "--port", "8004"]
