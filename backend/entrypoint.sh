#!/bin/sh
set -eu

echo "Running migrations..."
alembic upgrade head

if [ "${SEED_ALPHA_DATA:-true}" = "true" ]; then
  echo "Seeding alpha sample data..."
  python -m app.seed_alpha
fi

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
