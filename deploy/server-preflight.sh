#!/usr/bin/env sh
set -eu

missing=0

check_command() {
  name="$1"
  command="$2"
  if sh -c "command -v $command >/dev/null 2>&1"; then
    printf 'ok %s: ' "$name"
    sh -c "$command --version 2>&1 | head -1" || true
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
check_command "pnpm" "pnpm"
check_command "python3" "python3"
check_command "uv" "uv"
check_command "psql" "psql"
check_command "nginx" "nginx"

if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY'
import sys
version = sys.version_info
print(f"python3 version tuple: {version.major}.{version.minor}.{version.micro}")
if version < (3, 12):
    raise SystemExit("python3 must be 3.12+ for this project")
PY
fi

if [ "$missing" -ne 0 ]; then
  echo
  echo "preflight failed: install or provide the missing runtime commands before deployment"
  exit 1
fi

echo
echo "preflight passed"
