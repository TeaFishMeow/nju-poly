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
export UV_CONCURRENT_DOWNLOADS="${UV_CONCURRENT_DOWNLOADS:-1}"
export UV_CONCURRENT_BUILDS="${UV_CONCURRENT_BUILDS:-1}"
export UV_CONCURRENT_INSTALLS="${UV_CONCURRENT_INSTALLS:-1}"

cd "$ROOT"
./deploy/api-production-check.sh

cd "$ROOT/apps/api"
uv run --frozen alembic upgrade head
