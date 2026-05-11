"""
Multi-Agent PPT Generation Pipeline

Pipeline:
    Travel Plan Text → JSON Structurer → Slide Planner → Visual Assets
    → PPT Renderer → .pptx bytes

LLM only generates structured data. Rendering is programmatic.
"""
import json
import logging

from app.agent.state import AgentState
from app.core.llm_client import chat_completion
from app.ppt.renderer import render_pptx

logger = logging.getLogger(__name__)


def _clean_json_response(content: str) -> str:
    return content.strip().removeprefix("```json").removesuffix("```").strip()


# ---- Agent 1: JSON Structurer ----
STRUCTURER_PROMPT = """You are a travel data extraction engine. Convert the travel plan below into strict JSON.

Output ONLY valid JSON. No explanations. No markdown fences.

Schema:
{{
  "title": "short trip title",
  "destination": "main destination",
  "duration_days": 3,
  "travel_style": "cultural / beach / adventure / etc",
  "traveler_type": "couple / family / solo / etc",
  "budget": {{"total": "5000 CNY", "per_person": "2500 CNY"}},
  "days": [
    {{
      "day": 1,
      "theme": "Arrival & First Taste",
      "city": "city name",
      "activities": ["activity 1", "activity 2"],
      "foods": [{{"name": "restaurant", "cuisine": "local", "cost": "60 CNY"}}],
      "hotel": {{"name": "Hotel Name", "area": "central", "cost_per_night": "300 CNY"}},
      "transportation": [{{"from": "Airport", "to": "Hotel", "mode": "taxi", "cost": "80 CNY"}}]
    }}
  ]
}}

Travel plan:
{travel_plan}"""


async def structurer_node(state: AgentState) -> AgentState:
    plan = state.get("final_response", state.get("draft_plan", ""))
    response = await chat_completion([
        {"role": "user", "content": STRUCTURER_PROMPT.format(travel_plan=plan[:8000])}
    ])
    content = _clean_json_response(response.get("content", "{}"))
    try:
        state["travel_json"] = json.loads(content)
    except json.JSONDecodeError:
        state["travel_json"] = {"error": "JSON parse failed", "raw": content[:500]}
    return state


# ---- Agent 2: Slide Planner ----
SLIDE_PLANNER_PROMPT = """You are a presentation architect. Transform travel data into slide DSL.

Output ONLY valid JSON. No markdown fences.

Rules:
- 1 slide = 1 core message
- No large paragraphs
- Prefer cards, timelines, bullet groups, tables
- Max 12 slides total
- Include: cover, overview, 1 slide per day, food, hotel, budget, transport, tips, ending
- Theme name: minimal / japan / tropical / ocean / editorial / nature (pick best fit)

Output:
{{
  "theme": "tropical",
  "slides": [
    {{
      "slide_type": "cover",
      "title": "Phuket 5-Day Escape",
      "subtitle": "Beach · Island Hopping · Thai Food",
      "layout": "hero"
    }},
    {{
      "slide_type": "timeline",
      "title": "Itinerary Overview",
      "subtitle": "Day-by-day plan",
      "layout": "timeline",
      "days": [
        {{"day": 1, "theme": "Arrival & Sunset", "activities": ["Airport → Hotel", "Beach sunset", "Night market"]}}
      ]
    }},
    {{
      "slide_type": "food",
      "title": "Must-Try Foods",
      "layout": "cards",
      "items": [
        {{"name": "Tom Yum Goong", "desc": "Spicy sour shrimp soup - a Thai classic"}}
      ]
    }},
    {{
      "slide_type": "budget",
      "title": "Budget Breakdown",
      "layout": "table",
      "items": [
        {{"category": "Flights", "detail": "Round trip BKK-HKT", "amount": "1,200 CNY"}}
      ],
      "total": "Total: 4,500 CNY (2,250/person)"
    }},
    {{
      "slide_type": "ending",
      "title": "Safe Travels! 🏝️",
      "subtitle": "Your Phuket adventure awaits"
    }}
  ]
}}

Travel data:
{travel_json}"""


async def slide_planner_node(state: AgentState) -> AgentState:
    travel_json = json.dumps(state.get("travel_json", {}), ensure_ascii=False)
    response = await chat_completion([
        {"role": "user", "content": SLIDE_PLANNER_PROMPT.format(travel_json=travel_json[:6000])}
    ])
    content = _clean_json_response(response.get("content", "{}"))
    try:
        slide_data = json.loads(content)
        state["slide_dsl"] = slide_data.get("slides", [])
        state["slide_theme"] = slide_data.get("theme", "minimal")
    except json.JSONDecodeError:
        state["slide_dsl"] = []
        state["slide_theme"] = "minimal"
    return state


# ---- Agent 3: Visual Asset ----
VISUAL_PROMPT = """Generate image search queries for presentation slides.

Output ONLY valid JSON:
{{
  "assets": [
    {{"slide_index": 0, "queries": ["Thailand beach sunset cinematic wide"]}},
    {{"slide_index": 1, "queries": ["Phuket island map"]}}
  ]
}}

Slides:
{slides_json}"""


async def visual_asset_node(state: AgentState) -> AgentState:
    slides = state.get("slide_dsl", [])
    if not slides:
        state["visual_assets"] = []
        return state

    slides_json = json.dumps(slides[:6], ensure_ascii=False)
    response = await chat_completion([
        {"role": "user", "content": VISUAL_PROMPT.format(slides_json=slides_json)}
    ])
    content = _clean_json_response(response.get("content", "{}"))
    try:
        state["visual_assets"] = json.loads(content).get("assets", [])
        logger.info("Visual asset queries generated: %d asset groups for %d slides",
                     len(state["visual_assets"]),
                     sum(1 for a in state["visual_assets"] if a.get("queries")))
    except json.JSONDecodeError:
        state["visual_assets"] = []
    return state


# ---- Pipeline Orchestrator ----

async def generate_pptx_stream(plan_text: str):
    """Yield progress events during PPT generation. Yields final state as last event."""
    state = _init_state(plan_text)

    yield {"type": "progress", "stage": "structurer", "msg": "正在解析旅行计划..."}
    state = await structurer_node(state)

    yield {"type": "progress", "stage": "planner", "msg": "正在设计幻灯片布局..."}
    state = await slide_planner_node(state)

    yield {"type": "progress", "stage": "assets", "msg": "正在搜索相关图片..."}
    state = await visual_asset_node(state)

    yield {"type": "progress", "stage": "render", "msg": "正在生成PPT文件..."}
    yield {"type": "_pipeline_state", "state": state}


def _init_state(plan_text: str) -> AgentState:
    return {
        "final_response": plan_text,
        "travel_json": {},
        "slide_dsl": [],
        "slide_theme": "minimal",
        "visual_assets": [],
        "node_history": [],
    }


async def generate_pptx(plan_text: str, *, state: AgentState | None = None) -> bytes:
    """Run the full pipeline and return .pptx bytes.

    If `state` is provided (from a prior stream), skips LLM nodes and renders directly.
    """
    if state is None:
        state = _init_state(plan_text)
        state = await structurer_node(state)
        state = await slide_planner_node(state)
        state = await visual_asset_node(state)

    return await _render_from_state(state)


async def _render_from_state(state: AgentState) -> bytes:
    slides = state.get("slide_dsl", [])
    theme = state.get("slide_theme", "minimal")

    if not slides:
        slides = _fallback_slides(state.get("travel_json", {}))
        theme = "minimal"

    assets = state.get("visual_assets", [])
    return await render_pptx(slides, theme, assets)


def _fallback_slides(travel_json: dict) -> list[dict]:
    """Generate minimal slides when Slide Planner fails."""
    slides = [
        {"slide_type": "cover", "title": travel_json.get("title", "Travel Plan"),
         "subtitle": f"{travel_json.get('destination', '')} · {travel_json.get('duration_days', 3)} days"}
    ]
    for day in travel_json.get("days", []):
        slides.append({
            "slide_type": "timeline", "title": f"Day {day.get('day', '?')}",
            "subtitle": day.get("theme", ""), "layout": "timeline",
            "days": [day]
        })
    slides.append({"slide_type": "ending", "title": "Bon Voyage! ✈️", "subtitle": "Have a wonderful trip"})
    return slides
