"""
PPT Renderer — Programmatic PPTX generation from Slide DSL.

Rule: The renderer is NOT an LLM. It follows template constraints.
"""
import io
import httpx
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from app.core.config import settings

# ---- Image fetching via Tavily ----
IMAGE_CACHE: dict[str, bytes] = {}

async def _fetch_images(queries: list[str]) -> list[bytes]:
    """Search images via Tavily and download them. Returns list of image bytes."""
    if not settings.tavily_api_key:
        return await _fallback_images(queries)

    results = []
    for q in queries[:3]:
        if q in IMAGE_CACHE:
            results.append(IMAGE_CACHE[q])
            continue
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=settings.tavily_api_key)
            resp = client.search(query=q, search_depth="basic", include_images=True, max_results=3)
            image_urls = resp.get("images", [])
            if image_urls:
                img_bytes = await _download_image(image_urls[0])
                if img_bytes:
                    IMAGE_CACHE[q] = img_bytes
                    results.append(img_bytes)
        except Exception:
            pass
    return results


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
    """Fallback: Unsplash when Tavily not configured."""
    results = []
    for q in queries[:2]:
        if q in IMAGE_CACHE:
            results.append(IMAGE_CACHE[q])
            continue
        try:
            url = f"https://source.unsplash.com/800x600/?{q}"
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.content) > 2000:
                    IMAGE_CACHE[q] = resp.content
                    results.append(resp.content)
        except Exception:
            pass
    return results


def _embed_image(slide, image_bytes: bytes, left, top, width, height):
    """Embed an image into a slide."""
    import io as _io
    try:
        slide.shapes.add_picture(_io.BytesIO(image_bytes),
                                 Inches(left), Inches(top),
                                 Inches(width), Inches(height))
    except Exception:
        rect = slide.shapes.add_shape(
            1, Inches(left), Inches(top), Inches(width), Inches(height))
        rect.fill.solid()
        rect.fill.fore_color.rgb = _color("E8E8E8")
        rect.line.fill.background()

# ---- Theme System ----
THEMES = {
    "japan": {"bg": "F5F0E8", "accent": "9B1B30", "text": "2D2D2D", "sub": "8B7355"},
    "minimal": {"bg": "FFFFFF", "accent": "111111", "text": "1A1A1A", "sub": "757575"},
    "tropical": {"bg": "FFF8F0", "accent": "E8734A", "text": "2C3E50", "sub": "8E6E53"},
    "ocean": {"bg": "F0F4F8", "accent": "1B4F72", "text": "1C2833", "sub": "5D6D7E"},
    "editorial": {"bg": "FAFAFA", "accent": "2C3E50", "text": "1A1A1A", "sub": "7F8C8D"},
    "nature": {"bg": "F4F6F0", "accent": "3E6B48", "text": "2D3436", "sub": "6B7F6B"},
}

DEFAULT_THEME = THEMES["minimal"]

WIDTH = Inches(13.333)
HEIGHT = Inches(7.5)


def _color(hex_str: str) -> RGBColor:
    return RGBColor(int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


async def render_pptx(slides: list[dict], theme_name: str = "minimal",
                     assets: list[dict] | None = None) -> bytes:
    """Render a list of slide DSL dicts into a .pptx file. Returns bytes."""
    prs = Presentation()
    prs.slide_width = WIDTH
    prs.slide_height = HEIGHT

    theme = THEMES.get(theme_name, DEFAULT_THEME)
    assets = assets or []

    blank_layout = prs.slide_layouts[6]  # blank

    for idx, s in enumerate(slides):
        slide_type = s.get("slide_type", "content")
        slide = prs.slides.add_slide(blank_layout)
        _set_bg(slide, theme["bg"])

        # Find matching asset for this slide
        asset_queries = []
        for a in assets:
            if a.get("slide_index") == idx:
                asset_queries = a.get("queries", [])
                break

        if slide_type == "cover":
            await _render_cover(slide, s, theme, asset_queries)
        elif slide_type in ("overview", "itinerary", "timeline"):
            _render_timeline(slide, s, theme)
        elif slide_type in ("food", "hotel", "tips"):
            _render_cards(slide, s, theme)
        elif slide_type == "budget":
            _render_budget(slide, s, theme)
        elif slide_type == "ending":
            _render_ending(slide, s, theme)
        elif slide_type == "map":
            await _render_map_slide(slide, s, theme, asset_queries)
        else:
            _render_content(slide, s, theme)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.read()


def _set_bg(slide, color: str):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = _color(color)


def _add_text_box(slide, left, top, width, height, text, font_size=18, bold=False,
                  color="2D2D2D", align=PP_ALIGN.LEFT, font_name="Arial"):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = _color(color)
    p.font.name = font_name
    p.alignment = align
    return tf


# ---- Slide Renderers ----

async def _render_cover(slide, s, theme, asset_queries: list[str]):
    title = s.get("title", "Travel Plan")
    subtitle = s.get("subtitle", "")

    # Fetch cover image
    images = await _fetch_images(asset_queries)
    if images:
        _embed_image(slide, images[0], 6.8, 0, 6.6, 7.5)
        # Left panel overlay for text readability
        panel = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(7.2), Inches(7.5))
        panel.fill.solid()
        panel.fill.fore_color.rgb = _color(theme["bg"])
        panel.line.fill.background()

    _add_text_box(slide, 0.8, 2.2, 5.5, 1.5, title, 44, True, theme["accent"],
                  PP_ALIGN.LEFT, "Arial Black")
    if subtitle:
        _add_text_box(slide, 0.8, 3.7, 5, 0.8, subtitle, 20, False, theme["sub"])
    line = slide.shapes.add_shape(1, Inches(0.8), Inches(4.7), Inches(3), Inches(0.04))
    line.fill.solid()
    line.fill.fore_color.rgb = _color(theme["accent"])
    line.line.fill.background()


def _render_timeline(slide, s, theme):
    title = s.get("title", "Itinerary")
    subtitle = s.get("subtitle", "")
    days = s.get("days", [])
    _add_text_box(slide, 0.8, 0.4, 11, 0.7, title, 28, True, theme["text"])
    if subtitle:
        _add_text_box(slide, 0.8, 1.0, 11, 0.5, subtitle, 16, False, theme["sub"])

    # Timeline layout: Day columns
    n = len(days)
    if n == 0:
        return
    col_w = 11.5 / n
    for i, day in enumerate(days):
        x = 0.8 + i * col_w
        # Day header
        _add_text_box(slide, x, 1.8, col_w - 0.3, 0.4,
                      f"Day {day.get('day', i+1)}", 18, True, theme["accent"])
        _add_text_box(slide, x, 2.2, col_w - 0.3, 0.8,
                      day.get("theme", ""), 14, False, theme["sub"])
        # Activities (max 4 to avoid overflow)
        activities = day.get("activities", [])
        y = 3.1
        for j, act in enumerate(activities[:4]):
            _add_text_box(slide, x, y, col_w - 0.3, 0.6,
                          f"• {act[:60]}", 11, False, theme["text"])
            y += 0.7


def _render_cards(slide, s, theme):
    title = s.get("title", "")
    items = s.get("items", [])
    _add_text_box(slide, 0.8, 0.4, 11, 0.7, title, 28, True, theme["text"])

    # Normalize items: strings → {name: str, desc: ""}
    normalized = []
    for item in items:
        if isinstance(item, str):
            normalized.append({"name": item[:60], "desc": ""})
        elif isinstance(item, dict):
            normalized.append({
                "name": str(item.get("name", item.get("title", "")))[:60],
                "desc": str(item.get("desc", item.get("subtitle", "")))[:120]
            })
    items = normalized

    n = len(items)
    if n == 0:
        return
    cols = 2 if n <= 4 else 3
    col_w = 11.5 / cols
    for i, item in enumerate(items):
        row = i // cols
        col = i % cols
        x = 0.8 + col * col_w
        y = 1.6 + row * 2.5
        card = slide.shapes.add_shape(
            1, Inches(x), Inches(y), Inches(col_w - 0.4), Inches(2.0))
        card.fill.solid()
        card.fill.fore_color.rgb = _color("FFFFFF")
        card.line.color.rgb = _color("E0E0E0")
        card.line.width = Pt(0.5)
        _add_text_box(slide, x + 0.2, y + 0.15, col_w - 0.8, 0.4,
                      item["name"][:40], 16, True, theme["accent"])
        _add_text_box(slide, x + 0.2, y + 0.7, col_w - 0.8, 1.0,
                      item["desc"][:120], 11, False, theme["text"])


def _render_budget(slide, s, theme):
    title = s.get("title", "Budget")
    items = s.get("items", [])
    total = s.get("total", "")
    _add_text_box(slide, 0.8, 0.4, 11, 0.7, title, 28, True, theme["text"])

    # Table-like layout
    headers = ["类别", "明细", "金额"]
    col_widths = [2.5, 6.0, 3.0]
    x_positions = [0.8]
    for w in col_widths[:-1]:
        x_positions.append(x_positions[-1] + w)

    y = 1.6
    # Header row
    for j, h in enumerate(headers):
        _add_text_box(slide, x_positions[j], y, col_widths[j], 0.4,
                      h, 13, True, theme["accent"])
    y += 0.5
    # Data rows
    for item in items[:8]:
        if isinstance(item, str):
            _add_text_box(slide, 0.8, y, 11, 0.35, f"• {item[:80]}", 12, False, theme["text"])
        else:
            for j, key in enumerate(["category", "detail", "amount"]):
                _add_text_box(slide, x_positions[j], y, col_widths[j], 0.35,
                              str(item.get(key, ""))[:50], 12, False, theme["text"])
        y += 0.4

    if total:
        _add_text_box(slide, 0.8, y + 0.2, 11, 0.4, total, 16, True, theme["accent"])


async def _render_map_slide(slide, s, theme, asset_queries: list[str]):
    title = s.get("title", "Route Map")
    _add_text_box(slide, 0.8, 0.4, 11, 0.7, title, 28, True, theme["text"])

    images = await _fetch_images(asset_queries)
    if images:
        _embed_image(slide, images[0], 0.8, 1.5, 11.5, 5.5)
    else:
        _add_text_box(slide, 0.8, 2.5, 11.5, 4.0,
                      s.get("description", "路线示意图"),
                      14, False, theme["sub"])


def _render_ending(slide, s, theme):
    _add_text_box(slide, 1.5, 2.8, 10, 1.0, s.get("title", "Bon Voyage! ✈️"),
                  42, True, theme["accent"], PP_ALIGN.CENTER, "Arial Black")
    _add_text_box(slide, 1.5, 3.8, 10, 0.6, s.get("subtitle", "Have a wonderful trip"),
                  20, False, theme["sub"], PP_ALIGN.CENTER)


def _render_content(slide, s, theme):
    title = s.get("title", "")
    bullets = s.get("bullets", [])
    _add_text_box(slide, 0.8, 0.4, 11, 0.7, title, 28, True, theme["text"])
    y = 1.6
    for b in bullets[:8]:
        _add_text_box(slide, 1.2, y, 10.5, 0.5, f"• {b[:100]}", 14, False, theme["text"])
        y += 0.55
