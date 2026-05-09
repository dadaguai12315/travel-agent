import json

from tavily import TavilyClient

from app.config import settings

_client = TavilyClient(api_key=settings.tavily_api_key) if settings.tavily_api_key else None

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "在互联网上搜索最新、真实的旅行相关信息。"
                "当需要获取实时数据（天气、价格、签证政策、活动）或补充目的地细节时使用。"
                "可以同时搜索多个查询词条以提高效率。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "搜索查询词条列表。每条查询应具体明确，用中文。"
                            "示例：['巴厘岛 12月 天气 气温', '巴厘岛 蜜月酒店 价格 2025', "
                            "'中国公民 印尼 最新免签政策']"
                        ),
                    },
                },
                "required": ["queries"],
            },
        },
    },
] if _client else []


def search_enabled() -> bool:
    """Check if web search is available."""
    return _client is not None


def execute_web_search(queries: list[str]) -> list[dict]:
    """Execute multiple web search queries and return merged results."""
    if not _client:
        return [{"error": "搜索服务未配置（缺少 TAVILY_API_KEY）"}]

    all_results = []
    for q in queries:
        try:
            response = _client.search(
                query=q,
                search_depth="basic",
                max_results=3,
                include_answer=True,
            )
            result = {
                "query": q,
                "answer": response.get("answer", ""),
                "results": [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", ""),
                    }
                    for r in response.get("results", [])
                ],
            }
            all_results.append(result)
        except Exception as e:
            all_results.append({"query": q, "error": str(e)})

    return all_results


TOOL_EXECUTORS = {
    "web_search": lambda **kwargs: execute_web_search(**kwargs),
}


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name and return JSON string result."""
    executor = TOOL_EXECUTORS.get(name)
    if not executor:
        return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)

    try:
        result = executor(**arguments)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
