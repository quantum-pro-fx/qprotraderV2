# Multi-stage build for optimal image size
FROM python:3.11-slim as builder

WORKDIR /app
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# --- Runtime stage ---
FROM python:3.11-slim

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH

# Copy installed Python packages
COPY --from=builder /root/.local /root/.local

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Environment variables (override with docker-compose or runtime)
ENV REDIS_URL=redis://redis:6379
ENV OANDA_ENVIRONMENT=practice

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import redis; redis.Redis.from_url('$REDIS_URL').ping()" || exit 1

COPY docker/entrypoint.sh /entrypoint.sh
COPY scripts/initialize.py /app/scripts/initialize.py
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "main.py"]