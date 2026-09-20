#!/usr/bin/env sh
# Entrypoint for the LearnSphere backend container.
# Runs database migrations, then starts uvicorn on the port Render provides.
set -e

echo "[entrypoint] Running database migrations..."
alembic upgrade head

PORT="${PORT:-8000}"
echo "[entrypoint] Starting uvicorn on 0.0.0.0:${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --proxy-headers --forwarded-allow-ips='*'
