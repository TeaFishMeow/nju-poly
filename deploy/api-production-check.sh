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

cd "$ROOT/apps/api"

uv run --frozen python - <<'PY'
import asyncio
from urllib.parse import urlsplit

from pydantic_core import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

try:
    from app.core.config import settings
except ValidationError as error:
    missing = []
    for item in error.errors():
        location = item.get("loc", ())
        if item.get("type") == "missing" and location:
            missing.append(str(location[0]).upper())

    if missing:
        raise SystemExit("missing production value: " + ", ".join(sorted(missing))) from None

    raise SystemExit("invalid production environment configuration") from None


def require(name: str, value: str | None) -> None:
    if not value or value.startswith("REPLACE_") or value.startswith("REPLACE_WITH_"):
        raise SystemExit(f"missing production value: {name}")


require("DATABASE_URL", settings.database_url)
require("CORS_ORIGINS", settings.cors_origins)
require("SESSION_TOKEN_SECRET", settings.session_token_secret)
require("SMTP_HOST", settings.smtp_host)
require("SMTP_USERNAME", settings.smtp_username)
require("SMTP_PASSWORD", settings.smtp_password)
require("SMTP_FROM", settings.smtp_from)
require("IMAGE_MODEL_API_KEY", settings.image_model_api_key)

if not settings.database_url.startswith("postgresql+asyncpg://"):
    raise SystemExit("DATABASE_URL must use postgresql+asyncpg:// in production")

if "https://polymarket.exnju.top" not in settings.cors_origin_list:
    raise SystemExit("CORS_ORIGINS must include https://polymarket.exnju.top")

if len(settings.session_token_secret) < 32:
    raise SystemExit("SESSION_TOKEN_SECRET must be at least 32 characters")

if settings.smtp_use_tls and settings.smtp_use_ssl:
    raise SystemExit("SMTP_USE_TLS and SMTP_USE_SSL cannot both be true")


async def main() -> None:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
    finally:
        await engine.dispose()


asyncio.run(main())

database = urlsplit(settings.database_url)
safe_database = database.hostname or "configured-host"
if database.port:
    safe_database = f"{safe_database}:{database.port}"

print("production config: ok")
print(f"database connectivity: ok ({safe_database})")
print(f"cors origins: {', '.join(settings.cors_origin_list)}")
print(f"smtp: configured ({settings.smtp_host}:{settings.smtp_port})")
print(f"image model: configured ({settings.image_model_name})")
PY
