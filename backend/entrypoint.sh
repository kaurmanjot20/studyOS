#!/usr/bin/env bash
set -euo pipefail

echo "==> Waiting for database..."
python -m app.db.wait_for_db

echo "==> Running migrations..."
alembic upgrade head

echo "==> Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
