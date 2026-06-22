from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from sqlalchemy import select

from app.core.config import settings
from app.db.session import async_session
from app.markets.models import Event, EventStatus

ROOT = Path(__file__).resolve().parents[3]
WEB_PUBLIC_DIR = ROOT / "apps" / "web" / "public"
WEB_BRAND_DIR = WEB_PUBLIC_DIR / "brand"
WEB_BRAND_MANIFEST = WEB_BRAND_DIR / "brand-art.json"
WEB_GOAL7_MANIFEST = WEB_BRAND_DIR / "goal7-art-manifest.json"
WEB_BRAND_CODE = ROOT / "apps" / "web" / "src" / "generated" / "brand-art.ts"

RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _fail(message: str) -> None:
    raise SystemExit(message)


def _is_raster_image(path: Path) -> bool:
    data = path.read_bytes()[:16]
    return (
        data.startswith(b"\x89PNG\r\n\x1a\n")
        or data.startswith(b"\xff\xd8\xff")
        or (data.startswith(b"RIFF") and data[8:12] == b"WEBP")
    )


def _load_json(path: Path) -> dict:
    if not path.exists():
        _fail(f"missing art manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _media_file_from_url(url: str) -> Path:
    if not url.startswith(f"{settings.media_public_base_url.rstrip('/')}/"):
        _fail(f"media url does not use configured public base: {url}")
    filename = url.rsplit("/", maxsplit=1)[-1]
    return Path(settings.media_storage_dir) / filename


def _assert_raster(path: Path, *, label: str) -> None:
    if not path.exists():
        _fail(f"missing {label}: {path}")
    if path.suffix.lower() not in RASTER_SUFFIXES:
        _fail(f"{label} is not a raster asset: {path}")
    if not _is_raster_image(path):
        _fail(f"{label} does not have a recognized raster image signature: {path}")


async def main() -> None:
    brand_manifest = _load_json(WEB_BRAND_MANIFEST)
    goal7_manifest = _load_json(WEB_GOAL7_MANIFEST)

    logo_path = brand_manifest.get("logo", {}).get("publicPath")
    if not isinstance(logo_path, str) or not logo_path.startswith("/brand/"):
        _fail("brand manifest logo.publicPath must point at /brand/<file>")
    if goal7_manifest.get("logo") != logo_path:
        _fail("goal7-art-manifest logo does not match brand-art manifest")

    brand_code = WEB_BRAND_CODE.read_text(encoding="utf-8") if WEB_BRAND_CODE.exists() else ""
    if logo_path not in brand_code:
        _fail("generated frontend brand-art.ts does not reference the selected logo")
    _assert_raster(WEB_PUBLIC_DIR / logo_path.lstrip("/"), label="selected logo")

    manifest_covers = goal7_manifest.get("covers")
    if not isinstance(manifest_covers, list):
        _fail("goal7-art-manifest covers must be a list")
    manifest_by_slug = {cover.get("slug"): cover for cover in manifest_covers if isinstance(cover, dict)}

    async with async_session() as session:
        events = (
            await session.scalars(
                select(Event).where(Event.status != EventStatus.REJECTED).order_by(Event.id)
            )
        ).all()

    missing_manifest_slugs: list[str] = []
    verified_covers: list[str] = []
    for event in events:
        if not event.cover_url:
            _fail(f"event has no generated cover_url: {event.slug}")
        if event.cover_url.endswith(".svg"):
            _fail(f"event cover_url still points at SVG fallback: {event.slug} -> {event.cover_url}")
        cover = manifest_by_slug.get(event.slug)
        if not cover:
            missing_manifest_slugs.append(event.slug)
            continue
        if cover.get("coverUrl") != event.cover_url:
            _fail(f"manifest coverUrl differs from database for event: {event.slug}")
        _assert_raster(_media_file_from_url(event.cover_url), label=f"cover for {event.slug}")
        verified_covers.append(event.slug)

    if missing_manifest_slugs:
        _fail(f"goal7-art-manifest is missing event covers: {', '.join(missing_manifest_slugs)}")

    print(
        json.dumps(
            {
                "logo": logo_path,
                "verifiedCoverCount": len(verified_covers),
                "verifiedCovers": verified_covers,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
