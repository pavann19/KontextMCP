# Application image; local credentials and runtime records are excluded by .dockerignore.
FROM python:3.11-slim@sha256:65bd3d9f1d7fa268dd1909973ba7eb4bdf41f6dcf2cfbe76ba9528b170f3fd79 AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt requirements-linux.lock requirements-bootstrap.lock requirements-mcp-client.txt requirements-mcp-client.lock ./
RUN pip install --no-cache-dir -r requirements-bootstrap.lock \
    && pip install --no-cache-dir -r requirements-linux.lock \
    && python -m venv /opt/mcp-sdk \
    && /opt/mcp-sdk/bin/pip install --no-cache-dir -r requirements-bootstrap.lock \
    && /opt/mcp-sdk/bin/pip install --no-cache-dir -r requirements-mcp-client.lock \
    && mkdir -p /opt/kontext-build \
    && python -m pip check > /opt/kontext-build/app-pip-check.txt \
    && /opt/mcp-sdk/bin/python -m pip check > /opt/kontext-build/sdk-pip-check.txt \
    && /opt/mcp-sdk/bin/python -m pip uninstall -y pip \
    && python -m pip uninstall -y pip
ENV MCP_SDK_PYTHON=/opt/mcp-sdk/bin/python

# Copy application source code
COPY . .
RUN groupadd --gid 10001 appuser && useradd --uid 10001 --gid 10001 --no-create-home appuser \
    && mkdir -p /var/lib/kontext /app/data \
    && chown -R 10001:10001 /var/lib/kontext /app/data
USER 10001:10001

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ready || exit 1

# Start FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--limit-concurrency", "64", "--timeout-graceful-shutdown", "30"]

