from __future__ import annotations

from pathlib import Path
from urllib import request
import base64
import json
import os
import re
import ssl

import certifi

from app.core.config import settings


class MediaError(ValueError):
    pass


SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
IMAGE_REQUEST_TIMEOUT_SECONDS = 180
IMAGE_MODEL_BASE_URL = os.environ.get("IMAGE_MODEL_BASE_URL", "https://yunwu.ai/v1")
IMAGE_MODEL_NAME = os.environ.get("IMAGE_MODEL_NAME", "gpt-image-2")
IMAGE_MODEL_API_KEY = os.environ.get("IMAGE_MODEL_API_KEY")


def cover_prompt_for_event(*, title: str, description: str, category: str) -> str:
    return (
        "Create a clean campus prediction-market cover image for NJUPoly. "
        f"Category: {category}. Title: {title}. Description: {description}. "
        "Use campus notice-board realism, no text, no logos, rectangular web cover."
    )


def generate_image(prompt: str, *, slug: str, size: str = "1536x1024") -> str:
    if IMAGE_MODEL_API_KEY:
        return _generate_remote_image(prompt, slug=slug, size=size)
    return _generate_local_cover(prompt, slug=slug)


def _generate_remote_image(prompt: str, *, slug: str, size: str) -> str:
    endpoint = f"{IMAGE_MODEL_BASE_URL.rstrip('/')}/images/generations"
    payload = json.dumps(
        {
            "model": IMAGE_MODEL_NAME,
            "prompt": prompt,
            "size": size,
            "n": 1,
        }
    ).encode("utf-8")
    req = request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {IMAGE_MODEL_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=IMAGE_REQUEST_TIMEOUT_SECONDS, context=SSL_CONTEXT) as response:
        body = json.loads(response.read().decode("utf-8"))
    image = body["data"][0]
    if "url" in image:
        return _download_image(image["url"], slug=slug)
    if "b64_json" in image:
        return _write_image_bytes(base64.b64decode(image["b64_json"]), slug=slug, suffix=".png")
    raise MediaError("image model response did not include url or b64_json")


def _generate_local_cover(prompt: str, *, slug: str) -> str:
    safe_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", slug).strip("-") or "event"
    directory = Path(settings.media_storage_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{safe_slug}.svg"
    accent = "#0f766e"
    bg = "#f8fafc"
    text = prompt[:160].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    path.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="576" viewBox="0 0 1024 576">
  <rect width="1024" height="576" fill="{bg}"/>
  <rect x="48" y="48" width="928" height="480" rx="20" fill="#ffffff" stroke="#cbd5e1" stroke-width="3"/>
  <path d="M112 382 C250 270 358 456 512 338 C674 214 790 292 912 176" fill="none" stroke="{accent}" stroke-width="18" stroke-linecap="round"/>
  <circle cx="214" cy="176" r="54" fill="#e0f2fe"/>
  <circle cx="790" cy="384" r="70" fill="#ccfbf1"/>
  <text x="96" y="106" font-family="Arial, sans-serif" font-size="28" font-weight="700" fill="#0f172a">NJUPoly Market Cover</text>
  <text x="96" y="488" font-family="Arial, sans-serif" font-size="20" fill="#475569">{text}</text>
</svg>
""",
        encoding="utf-8",
    )
    return f"{settings.media_public_base_url.rstrip('/')}/{path.name}"


def _download_image(url: str, *, slug: str) -> str:
    req = request.Request(url, headers={"User-Agent": "NJUPoly/0.1"})
    with request.urlopen(req, timeout=IMAGE_REQUEST_TIMEOUT_SECONDS, context=SSL_CONTEXT) as response:
        content_type = response.headers.get("Content-Type", "")
        data = response.read()
    return _write_image_bytes(data, slug=slug, suffix=_image_suffix(data, content_type=content_type))


def _image_suffix(data: bytes, *, content_type: str = "") -> str:
    lowered_type = content_type.lower()
    if data.startswith(b"\x89PNG\r\n\x1a\n") or "png" in lowered_type:
        return ".png"
    if data.startswith(b"\xff\xd8\xff") or "jpeg" in lowered_type or "jpg" in lowered_type:
        return ".jpg"
    if (data.startswith(b"RIFF") and data[8:12] == b"WEBP") or "webp" in lowered_type:
        return ".webp"
    return ".png"


def _write_image_bytes(data: bytes, *, slug: str, suffix: str) -> str:
    directory = Path(settings.media_storage_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", slug).strip("-") or "generated"
    filename = f"{safe_slug}{suffix}"
    path = directory / filename
    path.write_bytes(data)
    return f"{settings.media_public_base_url.rstrip('/')}/{filename}"
