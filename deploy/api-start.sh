#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

if [ -f "$ROOT/.local/server-env.sh" ]; then
  . "$ROOT/.local/server-env.sh"
fi

export PATH="$ROOT/.tools/bin:$PATH"
export PNPM_HOME="${PNPM_HOME:-$ROOT/.tools/pnpm-home}"
export PNPM_STORE_DIR="${PNPM_STORE_DIR:-$ROOT/.pnpm-store}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT/.cache/uv}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$ROOT/.cache/uv-python}"

cd "$ROOT/apps/api"
uv run alembic upgrade head
exec uv run uvicorn app.main:app --host "${NJUPOLY_API_HOST:-127.0.0.1}" --port "${NJUPOLY_API_PORT:-8000}" --proxy-headers
