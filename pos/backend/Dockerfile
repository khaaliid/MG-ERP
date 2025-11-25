# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/pos/backend

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LOG_LEVEL=INFO
ENV LOG_DIR=/app/logs
ENV AUTH_SERVICE_URL=http://host.docker.internal:8004
ENV INVENTORY_SERVICE_URL=http://host.docker.internal:8002
ENV LEDGER_SERVICE_URL=http://host.docker.internal:8000
ENV ENVIRONMENT=production

# Expose port (POS runs on 8001)
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

# Run the application
CMD ["uvicorn", "pos.backend.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
