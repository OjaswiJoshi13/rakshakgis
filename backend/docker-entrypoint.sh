#!/bin/bash
set -e

# Run database migrations on container startup if AUTO_MIGRATE is true (default: true)
if [ "${AUTO_MIGRATE:-true}" = "true" ]; then
    echo "[Entrypoint] Checking database and running Alembic migrations..."
    alembic upgrade head || echo "[Entrypoint] Alembic migration notice: could not run migrations or tables already exist."
fi

# Seed Himalayan demo data if explicitly requested
if [ "${SEED_DEMO_DATA:-false}" = "true" ] && [ "${DATA_MODE}" = "demo" ]; then
    echo "[Entrypoint] Seeding initial Himalayan demo fixtures..."
    python -m app.data.seed || echo "[Entrypoint] Demo seed notice: skipped or completed."
fi

exec "$@"
