#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PNPM_VERSION="${PNPM_VERSION:-10.13.1}"
UV_INSTALLER_URL="${UV_INSTALLER_URL:-https://astral.sh/uv/install.sh}"
NPM_CONFIG_REGISTRY="${NPM_CONFIG_REGISTRY:-https://registry.npmmirror.com}"
UV_CONCURRENT_DOWNLOADS="${UV_CONCURRENT_DOWNLOADS:-1}"
UV_CONCURRENT_BUILDS="${UV_CONCURRENT_BUILDS:-1}"
UV_CONCURRENT_INSTALLS="${UV_CONCURRENT_INSTALLS:-1}"

cd "$ROOT"

mkdir -p \
  .tools/bin \
  .tools/pnpm \
  .tools/uv \
  .cache/uv \
  .cache/uv-python \
  .pnpm-store \
  apps/api/.local

if [ ! -x "$ROOT/.tools/bin/pnpm" ]; then
  npm install --prefix "$ROOT/.tools/pnpm" --registry "$NPM_CONFIG_REGISTRY" "pnpm@$PNPM_VERSION"
  ln -sf "../pnpm/node_modules/.bin/pnpm" "$ROOT/.tools/bin/pnpm"
fi

if [ ! -x "$ROOT/.tools/bin/uv" ]; then
  installer="$(mktemp)"
  curl -fsSL "$UV_INSTALLER_URL" -o "$installer"
  UV_INSTALL_DIR="$ROOT/.tools/uv" sh "$installer"
  rm -f "$installer"
  ln -sf "../uv/uv" "$ROOT/.tools/bin/uv"
fi

export PATH="$ROOT/.tools/bin:$PATH"
export PNPM_HOME="${PNPM_HOME:-$ROOT/.tools/pnpm-home}"
export PNPM_STORE_DIR="${PNPM_STORE_DIR:-$ROOT/.pnpm-store}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT/.cache/uv}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$ROOT/.cache/uv-python}"
export UV_CONCURRENT_DOWNLOADS
export UV_CONCURRENT_BUILDS
export UV_CONCURRENT_INSTALLS

if [ -n "${UV_INDEX_URL:-}" ]; then
  export UV_INDEX_URL
fi

pnpm --version
uv --version

pnpm install --frozen-lockfile --store-dir "$PNPM_STORE_DIR" --registry "$NPM_CONFIG_REGISTRY"

cd "$ROOT/apps/api"
uv sync --frozen --python 3.12
