# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy source
COPY src/ ./src/
COPY config/ ./config/

# Create data directory for SQLite persistence
RUN mkdir -p /app/data

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Default config directory will be overridden by volume mount
VOLUME ["/app/config", "/app/data"]

ENTRYPOINT ["python", "-m", "pitunnel.main"]
