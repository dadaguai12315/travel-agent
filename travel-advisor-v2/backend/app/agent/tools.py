import json
from typing import Any

from app.core.config import settings

# ---- Tool Schemas (OpenAI function-calling format) ----

TAVILY_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for real-time travel information. "
            "Use this to get current weather, prices, visa policies, events, "
            "and destination details. Supports batch queries for efficiency."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of search queries in Chinese or English. Be specific.",
                },
            },
            "required": ["queries"],
        },
    },
}

ALL_TOOL_SCHEMAS = [TAVILY_TOOL_SCHEMA]


# ---- Tool Executors ----

async def execute_web_search(queries: list[str]) -> list[dict]:
    """Execute web search via Tavily API. Returns structured results."""
    if not settings.tavily_api_key:
        return [{"query": q, "error": "Search not configured"} for q in queries]

    # Lazy import to avoid circular dependencies
    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.tavily_api_key)
    results = []
    for q in queries:
        try:
            response = client.search(query=q, search_depth="basic", max_results=3, include_answer=True)
            results.append({
                "query": q,
                "answer": response.get("answer", ""),
                "sources": [
                    {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")}
                    for r in response.get("results", [])
                ],
            })
        except Exception as e:
            results.append({"query": q, "error": str(e)})
    return results


# Registry: maps tool name → async executor function
TOOL_EXECUTORS: dict[str, Any] = {
    "web_search": execute_web_search,
}


def search_enabled() -> bool:
    return bool(settings.tavily_api_key)
