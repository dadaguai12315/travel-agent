"""
PPT Renderer — Image fetching + PptxGenJS bridge.

Fetches images (Tavily/Unsplash), serializes slide data + design to JSON,
delegates PPTX rendering to a Node.js PptxGenJS script.
"""
import asyncio
import json
import logging
import os
import subprocess
import tempfile

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter('%(levelname)s [ppt] %(message)s'))
    logger.addHandler(_h)

_RENDERER_JS = os.path.join(os.path.dirname(__file__), "renderer.js")

# ---- Image Cache ----
_IMAGE_CACHE: dict[str, bytes] = {}
_MAX_IMAGE_CACHE = 64


async def _fetch_images(queries: list[str]) -> list[bytes]:
    """Search images via Tavily and download them in parallel."""
    if not settings.tavily_api_key:
        return await _fallback_images(queries)

    async def _fetch_one(q: str) -> bytes | None:
        if q in _IMAGE_CACHE:
            return _IMAGE_CACHE[q]
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=settings.tavily_api_key)
            resp = client.search(query=q, search_depth="basic", include_images=True, max_results=3)
            image_urls = resp.get("images", [])
            if image_urls:
                logger.info("Tavily found %d images for '%s'", len(image_urls), q[:60])
                img_bytes = await _download_image(image_urls[0])
                if img_bytes:
                    _cache_image(q, img_bytes)
                    logger.info("Downloaded image %d bytes", len(img_bytes))
                    return img_bytes
                else:
                    logger.warning("Failed to download image from %s", image_urls[0][:80])
            else:
                logger.warning("Tavily returned no images for '%s'", q[:60])
        except Exception:
            logger.exception("Tavily search failed for '%s'", q[:60])
        return None

    results = await asyncio.gather(*(_fetch_one(q) for q in queries[:3]))
    return [r for r in results if r is not None]


def _cache_image(key: str, data: bytes) -> None:
    if len(_IMAGE_CACHE) >= _MAX_IMAGE_CACHE:
        _IMAGE_CACHE.pop(next(iter(_IMAGE_CACHE)))
    _IMAGE_CACHE[key] = data


async def _download_image(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and len(resp.content) > 2000:
                return resp.content
    except Exception:
        pass
    return None


async def _fallback_images(queries: list[str]) -> list[bytes]:
    logger.info("Using Unsplash fallback (no Tavily API key)")

    async def _fetch_one(q: str) -> bytes | None:
        if q in _IMAGE_CACHE:
            return _IMAGE_CACHE[q]
        try:
            url = f"https://source.unsplash.com/800x600/?{q}"
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.content) > 2000:
                    _cache_image(q, resp.content)
                    return resp.content
        except Exception:
            logger.exception("Unsplash download failed for '%s'", q[:60])
        return None

    results = await asyncio.gather(*(_fetch_one(q) for q in queries[:2]))
    return [r for r in results if r is not None]


# ---- Main Render Entry Point ----

async def render_pptx(slides: list[dict], theme: dict | None = None,
                      assets: list[dict] | None = None,
                      title: str = "Travel Plan",
                      destination: str = "",
                      duration: str = "") -> bytes:
    """Fetch images, build JSON, delegate to PptxGenJS, return .pptx bytes.

    Args:
        slides: List of slide dicts with type, title, content fields.
        theme: {"bg", "accent", "text", "sub"} hex color dict.
        assets: Visual asset queries [{slide_index, queries}].
        title: Presentation title.
        destination: Trip destination name.
        duration: Trip duration string.
    """
    theme = theme or {}
    assets = assets or []

    with tempfile.TemporaryDirectory(prefix="ppt_") as tmpdir:
        # Pre-fetch images for ALL slides that have asset queries
        image_futures = {}
        for idx, s in enumerate(slides):
            queries = _get_asset_queries(assets, idx)
            if queries:
                image_futures[idx] = asyncio.ensure_future(_fetch_images(queries))

        # Save downloaded images to temp dir
        for idx, s in enumerate(slides):
            if idx in image_futures:
                images = await image_futures[idx]
                if images:
                    img_path = os.path.join(tmpdir, f"slide_{idx}.jpg")
                    _save_image(images[0], img_path)
                    s["image"] = img_path

        # Normalize slides: map "slide_type" → "type"
        normalized_slides = []
        for s in slides:
            ns = dict(s)
            if "slide_type" in ns:
                ns["type"] = ns.pop("slide_type")
            normalized_slides.append(ns)

        # Build JSON input
        input_json = {
            "theme": {
                "bg": theme.get("bg", "FFFFFF"),
                "accent": theme.get("accent", "111111"),
                "text": theme.get("text", "1A1A1A"),
                "sub": theme.get("sub", "757575"),
            },
            "title": title,
            "destination": destination,
            "duration": duration,
            "slides": normalized_slides,
        }

        json_path = os.path.join(tmpdir, "input.json")
        pptx_path = os.path.join(tmpdir, "output.pptx")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(input_json, f, ensure_ascii=False)

        # Run PptxGenJS renderer
        logger.info("Rendering %d slides via PptxGenJS", len(slides))
        await _run_node(json_path, pptx_path)

        with open(pptx_path, "rb") as f:
            return f.read()


def _save_image(data: bytes, path: str) -> None:
    with open(path, "wb") as f:
        f.write(data)


async def _run_node(json_path: str, pptx_path: str) -> None:
    """Run the Node.js renderer script in a thread executor."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_node_sync, json_path, pptx_path)


def _run_node_sync(json_path: str, pptx_path: str) -> None:
    result = subprocess.run(
        ["node", _RENDERER_JS, json_path, pptx_path],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        logger.error("PptxGenJS failed: %s", result.stderr)
        raise RuntimeError(f"PptxGenJS render failed: {result.stderr}")
    if result.stdout:
        logger.info("PptxGenJS: %s", result.stdout.strip())


def _get_asset_queries(assets: list[dict], slide_index: int) -> list[str]:
    for a in assets:
        if a.get("slide_index") == slide_index:
            return a.get("queries", [])
    return []
