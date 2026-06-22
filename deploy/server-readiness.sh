#!/usr/bin/env sh
set -u

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
failed=0

check() {
  name="$1"
  shift
  printf '%s: ' "$name"
  if "$@" >/tmp/njupoly-readiness.out 2>&1; then
    echo "ok"
  else
    failed=1
    echo "fail"
    if [ -s /tmp/njupoly-readiness.out ]; then
      sed 's/^/  /' /tmp/njupoly-readiness.out
    else
      echo "  command exited nonzero without output"
    fi
  fi
}

check_optional() {
  name="$1"
  shift
  printf '%s: ' "$name"
  if "$@" >/tmp/njupoly-readiness.out 2>&1; then
    echo "ok"
  else
    echo "warn"
    if [ -s /tmp/njupoly-readiness.out ]; then
      sed 's/^/  /' /tmp/njupoly-readiness.out
    else
      echo "  command exited nonzero without output"
    fi
  fi
}

cd "$ROOT"

echo "NJUPoly server readiness"
echo "root: $ROOT"
echo "host: $(hostname)"
echo

check "git clean" sh -c "test -z \"$(git status --short)\""
check "runtime preflight" ./deploy/server-preflight.sh
check "production config and database" ./deploy/api-production-check.sh
check_optional "api systemd active" systemctl is-active njupoly-api
check_optional "api localhost health" curl -fsS http://127.0.0.1:8000/health
check_optional "nginx site config" test -f /etc/nginx/conf.d/njupoly-api.conf
check_optional "nginx syntax" nginx -t

rm -f /tmp/njupoly-readiness.out

if [ "$failed" -ne 0 ]; then
  echo
  echo "server readiness failed"
  exit 1
fi

echo
echo "server readiness passed"
