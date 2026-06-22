#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/../apps/api"
uv run alembic upgrade head
exec uv run uvicorn app.main:app --host "${NJUPOLY_API_HOST:-127.0.0.1}" --port "${NJUPOLY_API_PORT:-8000}" --proxy-headers
