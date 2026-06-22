from __future__ import annotations

import asyncio
import json
import re
import shutil
import sys
import time
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from sqlalchemy import select

import app.auth.models  # noqa: F401
import app.ledger.models  # noqa: F401
from app.core.config import settings
from app.db.session import async_session
from app.markets.models import Event, EventStatus
from app.media.service import cover_prompt_for_event, generate_image

ROOT = Path(__file__).resolve().parents[3]
WEB_BRAND_DIR = ROOT / "apps" / "web" / "public" / "brand"
WEB_BRAND_MANIFEST = WEB_BRAND_DIR / "brand-art.json"
WEB_GENERATED_DIR = ROOT / "apps" / "web" / "src" / "generated"
WEB_BRAND_CODE = WEB_GENERATED_DIR / "brand-art.ts"
RASTER_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")
COVER_SIZE = "1536x1024"


LOGO_PROMPT = """
Use case: logo-brand
Asset type: NJUPoly website app icon / brand mark
Primary request: Generate a polished raster logo mark for 南哪竞猜 NJUPoly, a campus entertainment prediction-market app.
Scene/backdrop: clean flat app-icon composition, no scene.
Subject: a compact campus gate silhouette fused with a probability trend line and YES/NO market bars.
Style/medium: vector-like high-end fintech brand mark rendered as a crisp bitmap.
Composition/framing: centered square icon, generous padding, works at 40px and 512px.
Lighting/mood: precise, confident, campus-tech.
Color palette: deep ink, market teal, small campus blue accent.
Text: no text.
Constraints: no currency symbol, no real-money symbolism, no watermark, no letters, no Chinese characters.
Avoid: stock exchange tickers, coins, banknotes, mascots, clutter.
""".strip()


def _media_file_from_url(url: str) -> Path:
    filename = url.rsplit("/", maxsplit=1)[-1]
    path = Path(settings.media_storage_dir) / filename
    if not path.exists():
        raise FileNotFoundError(f"generated media file not found: {path}")
    return path


def _safe_slug(slug: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", slug).strip("-") or "generated"


def _existing_media_url(slug: str) -> str | None:
    safe_slug = _safe_slug(slug)
    directory = Path(settings.media_storage_dir)
    for suffix in RASTER_SUFFIXES:
        path = directory / f"{safe_slug}{suffix}"
        if path.exists():
            return f"{settings.media_public_base_url.rstrip('/')}/{path.name}"
    return None


def _is_existing_raster_media_url(url: str | None) -> bool:
    if not url or not url.lower().endswith(RASTER_SUFFIXES):
        return False
    try:
        return _media_file_from_url(url).exists()
    except FileNotFoundError:
        return False


def _generate_or_reuse_image(prompt: str, *, slug: str, size: str) -> str:
    existing_url = _existing_media_url(slug)
    if existing_url:
        return existing_url

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            return generate_image(prompt, slug=slug, size=size)
        except Exception as exc:  # noqa: BLE001 - script should retry transient provider failures.
            last_error = exc
            print(f"image generation failed for {slug} on attempt {attempt}/3: {exc}", file=sys.stderr)
            if attempt < 3:
                time.sleep(5 * attempt)
    assert last_error is not None
    raise last_error


def _write_web_brand_code(*, logo_public_path: str) -> None:
    WEB_GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    WEB_BRAND_CODE.write_text(
        f"export const generatedBrandLogoPath = {json.dumps(logo_public_path)} as const;\n",
        encoding="utf-8",
    )


async def main() -> None:
    if not settings.image_model_api_key:
        raise SystemExit(
            "IMAGE_MODEL_API_KEY is not set. Put the ai.md image-model key in .env, then rerun: "
            "uv run python scripts/generate_goal7_art.py"
        )

    WEB_BRAND_DIR.mkdir(parents=True, exist_ok=True)

    logo_url = _generate_or_reuse_image(LOGO_PROMPT, slug="njupoly-logo", size="1024x1024")
    logo_media_file = _media_file_from_url(logo_url)
    logo_suffix = ".jpg" if logo_media_file.suffix.lower() == ".jpeg" else logo_media_file.suffix.lower()
    if logo_suffix not in {".png", ".jpg", ".webp"}:
        raise SystemExit(f"unsupported generated logo format: {logo_media_file.suffix}")
    logo_filename = f"njupoly-logo{logo_suffix}"
    logo_public_path = f"/brand/{logo_filename}"
    shutil.copyfile(logo_media_file, WEB_BRAND_DIR / logo_filename)
    _write_web_brand_code(logo_public_path=logo_public_path)
    WEB_BRAND_MANIFEST.write_text(
        json.dumps(
            {
                "logo": {
                    "publicPath": logo_public_path,
                    "sourceMediaUrl": logo_url,
                    "prompt": LOGO_PROMPT,
                    "model": settings.image_model_name,
                    "baseUrl": settings.image_model_base_url,
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    generated_covers: list[dict[str, str]] = []
    async with async_session() as session:
        events = (
            await session.scalars(
                select(Event).where(Event.status != EventStatus.REJECTED).order_by(Event.id)
            )
        ).all()
        for event in events:
            prompt = cover_prompt_for_event(title=event.title, description=event.description, category=event.category)
            cover_url = event.cover_url if _is_existing_raster_media_url(event.cover_url) else _generate_or_reuse_image(prompt, slug=event.slug, size=COVER_SIZE)
            event.cover_url = cover_url
            generated_covers.append({"slug": event.slug, "coverUrl": cover_url, "prompt": prompt})
            await session.commit()

    (WEB_BRAND_DIR / "goal7-art-manifest.json").write_text(
        json.dumps(
            {
                "logo": logo_public_path,
                "covers": generated_covers,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"logo": logo_public_path, "covers": generated_covers}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
