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
export UV_INDEX_URL="${UV_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
export UV_CONCURRENT_DOWNLOADS="${UV_CONCURRENT_DOWNLOADS:-1}"
export UV_CONCURRENT_BUILDS="${UV_CONCURRENT_BUILDS:-1}"
export UV_CONCURRENT_INSTALLS="${UV_CONCURRENT_INSTALLS:-1}"

missing=0

check_command() {
  name="$1"
  command="$2"
  version_command="${3:-$command --version}"
  if sh -c "command -v $command >/dev/null 2>&1"; then
    printf 'ok %s: ' "$name"
    sh -c "$version_command 2>&1 | head -1" || true
  else
    printf 'missing %s (%s)\n' "$name" "$command"
    missing=1
  fi
}

echo "NJUPoly production preflight"
echo "host: $(hostname)"
echo "user: $(whoami)"
echo "cwd:  $(pwd)"
echo

check_command "node" "node"
check_command "npm" "npm"
check_command "pnpm" "pnpm"
check_command "uv" "uv"
check_command "psql" "psql"
check_command "nginx" "nginx" "nginx -v"

if command -v uv >/dev/null 2>&1; then
  cd "$ROOT/apps/api"
  uv run --frozen python - <<'PY'
import sys
version = sys.version_info
print(f"uv python version tuple: {version.major}.{version.minor}.{version.micro}")
if version < (3, 12):
    raise SystemExit("uv-managed python must be 3.12+ for this project")
PY
fi

if [ "$missing" -ne 0 ]; then
  echo
  echo "preflight failed: install or provide the missing runtime commands before deployment"
  exit 1
fi

echo
echo "preflight passed"
