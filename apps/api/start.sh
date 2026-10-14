#!/bin/sh
set -e

echo "Running database migrations..."
uv run alembic upgrade head

echo "Starting API server..."
exec uv run uvicorn jevops.main:app --host 0.0.0.0 --port ${PORT:-8000}
