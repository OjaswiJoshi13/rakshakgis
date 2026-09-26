# RakshakGIS Backend Dockerfile
# Python 3.11 with native geospatial libraries (GDAL, GEOS, PROJ)

FROM python:3.11-slim-bookworm

# Prevent Python from buffering stdout/stderr and writing bytecode
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

# Install essential system utilities and geospatial native libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --default-timeout=100 -r /app/requirements.txt

# Create unprivileged system group and user
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# Copy backend application source code and tests with non-root ownership
COPY --chown=appuser:appgroup backend/ /app/

# Ensure application directory and entrypoint are owned by appuser
RUN chmod +x /app/docker-entrypoint.sh && \
    chown -R appuser:appgroup /app

# Switch to unprivileged user
USER appuser

# Expose FastAPI application port
EXPOSE 8000

# Native container healthcheck probing application health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Production command (unprivileged, single-process, without development hot-reload)
# Note: In development Compose, --reload is enabled via command override
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
