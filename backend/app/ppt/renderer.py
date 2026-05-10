"""
PPT Renderer — Programmatic PPTX generation from Slide DSL.

Rule: The renderer is NOT an LLM. It follows template constraints.
- enforce consistent spacing
- enforce typography hierarchy
- avoid text overflow
- preserve theme consistency
"""
import io
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

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


def render_pptx(slides: list[dict], theme_name: str = "minimal") -> bytes:
    """Render a list of slide DSL dicts into a .pptx file. Returns bytes."""
    prs = Presentation()
    prs.slide_width = WIDTH
    prs.slide_height = HEIGHT

    theme = THEMES.get(theme_name, DEFAULT_THEME)

    # Remove default blank layout and use a blank canvas
    blank_layout = prs.slide_layouts[6]  # blank

    for s in slides:
        slide_type = s.get("slide_type", "content")
        slide = prs.slides.add_slide(blank_layout)
        _set_bg(slide, theme["bg"])

        if slide_type == "cover":
            _render_cover(slide, s, theme)
        elif slide_type in ("overview", "itinerary", "timeline"):
            _render_timeline(slide, s, theme)
        elif slide_type in ("food", "hotel", "tips"):
            _render_cards(slide, s, theme)
        elif slide_type == "budget":
            _render_budget(slide, s, theme)
        elif slide_type == "ending":
            _render_ending(slide, s, theme)
        elif slide_type == "map":
            _render_map_slide(slide, s, theme)
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

def _render_cover(slide, s, theme):
    title = s.get("title", "Travel Plan")
    subtitle = s.get("subtitle", "")
    _add_text_box(slide, 1.5, 2.2, 10, 1.5, title, 48, True, theme["accent"],
                  PP_ALIGN.LEFT, "Arial Black")
    if subtitle:
        _add_text_box(slide, 1.5, 3.7, 8, 0.8, subtitle, 22, False, theme["sub"])
    # Accent line
    line = slide.shapes.add_shape(1, Inches(1.5), Inches(4.7), Inches(3), Inches(0.04))  # rectangle as line
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

    # Grid layout: 2-3 columns
    n = len(items)
    cols = 2 if n <= 4 else 3
    col_w = 11.5 / cols
    for i, item in enumerate(items):
        row = i // cols
        col = i % cols
        x = 0.8 + col * col_w
        y = 1.6 + row * 2.5
        # Card background
        card = slide.shapes.add_shape(
            1, Inches(x), Inches(y), Inches(col_w - 0.4), Inches(2.0))
        card.fill.solid()
        card.fill.fore_color.rgb = _color("FFFFFF")
        card.line.color.rgb = _color("E0E0E0")
        card.line.width = Pt(0.5)
        # Card content
        _add_text_box(slide, x + 0.2, y + 0.15, col_w - 0.8, 0.4,
                      item.get("name", item.get("title", ""))[:40], 16, True, theme["accent"])
        _add_text_box(slide, x + 0.2, y + 0.7, col_w - 0.8, 1.0,
                      item.get("desc", item.get("subtitle", ""))[:120], 11, False, theme["text"])


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
        for j, key in enumerate(["category", "detail", "amount"]):
            _add_text_box(slide, x_positions[j], y, col_widths[j], 0.35,
                          str(item.get(key, ""))[:50], 12, False, theme["text"])
        y += 0.4

    if total:
        _add_text_box(slide, 0.8, y + 0.2, 11, 0.4, total, 16, True, theme["accent"])


def _render_map_slide(slide, s, theme):
    title = s.get("title", "Route Map")
    _add_text_box(slide, 0.8, 0.4, 11, 0.7, title, 28, True, theme["text"])
    _add_text_box(slide, 0.8, 1.5, 11, 0.5, "🗺️ 路线示意图", 14, False, theme["sub"])
    # Placeholder for map
    _add_text_box(slide, 0.8, 2.5, 11.5, 4.0,
                  s.get("description", "主要城市 → 景点 → 餐厅\n按行程顺序连接"),
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
