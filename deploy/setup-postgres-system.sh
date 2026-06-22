#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DB_NAME="${NJUPOLY_DB_NAME:-njupoly}"
DB_USER="${NJUPOLY_DB_USER:-njupoly}"

case "$DB_NAME:$DB_USER" in
  *[!A-Za-z0-9_:]*)
    echo "database name and user must contain only letters, numbers, and underscores" >&2
    exit 1
    ;;
esac

if [ "$(id -u)" -ne 0 ]; then
  echo "setup-postgres-system.sh must run as root" >&2
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  dnf install -y postgresql-server postgresql-contrib
fi

if [ ! -s /var/lib/pgsql/data/PG_VERSION ]; then
  postgresql-setup --initdb
fi

systemctl enable --now postgresql

DB_PASSWORD="$(openssl rand -hex 24)"

if (cd / && runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'") | grep -q 1; then
  (cd / && runuser -u postgres -- psql -v ON_ERROR_STOP=1 -c "ALTER ROLE \"$DB_USER\" WITH LOGIN PASSWORD '$DB_PASSWORD';") >/dev/null
else
  (cd / && runuser -u postgres -- psql -v ON_ERROR_STOP=1 -c "CREATE ROLE \"$DB_USER\" WITH LOGIN PASSWORD '$DB_PASSWORD';") >/dev/null
fi

if ! (cd / && runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'") | grep -q 1; then
  (cd / && runuser -u postgres -- createdb -O "$DB_USER" "$DB_NAME")
fi

cd "$ROOT"
printf '%s' "postgresql+asyncpg://$DB_USER:$DB_PASSWORD@127.0.0.1:5432/$DB_NAME" \
  | node deploy/set-production-env.mjs --key DATABASE_URL --stdin
chmod 600 apps/api/.env

echo "postgresql service: $(systemctl is-active postgresql)"
echo "database configured: $DB_NAME"
echo "database user configured: $DB_USER"
echo "DATABASE_URL updated in apps/api/.env"
