"""
Researcher Node

Generates search queries based on user preferences and executes
web searches to gather real-time travel information.
"""

from app.agent.state import AgentState
from app.agent.tools import execute_web_search


def build_search_queries(prefs: dict, user_message: str) -> list[str]:
    """Build targeted search queries from extracted preferences.

    In Phase 4, this will be LLM-generated. For Phase 3, it's rule-based.
    """
    queries = []

    region = prefs.get("region", "")
    dest_type = prefs.get("destination_type", "")
    season = prefs.get("season", "")
    budget = prefs.get("budget", "")

    # Destination search
    if region == "中国":
        if dest_type == "海滩":
            queries.append(f"{season or '夏季'} 国内 海滩度假 目的地推荐 2025")
        elif dest_type == "自然风光":
            queries.append(f"{season or '夏季'} 国内 避暑 自然风景区 推荐 2025")
        elif dest_type == "文化古城":
            queries.append(f"国内 文化古城 旅行攻略 {season or ''} 2025")
        else:
            queries.append(f"{season or '夏季'} 国内旅游 目的地推荐 2025")

    # Budget search
    if budget == "经济":
        queries.append(f"国内 穷游 省钱攻略 人均2000以内 2025")
    elif budget == "奢华":
        queries.append(f"国内 奢华度假 高端酒店 推荐 2025")

    # Specific destination if mentioned
    import re
    cities = re.findall(r"([一-鿿]{2,4}(?:市|岛|山|古镇|古城))", user_message)
    for city in cities[:2]:
        queries.append(f"{city} 旅游攻略 交通 住宿 {season or ''} 2025")

    # Ensure at least one query
    if not queries:
        queries.append(f"国内旅游 推荐 {season or '夏季'} 2025")

    return queries[:4]  # Max 4 queries


async def run_researcher(state: AgentState) -> AgentState:
    """Research phase: generate search queries and execute them.

    In Phase 4, this will use LLM to decide what to search.
    For Phase 3, queries are generated via rule-based logic.
    """
    state["node_history"] = state.get("node_history", []) + ["researcher"]

    prefs = state.get("extracted_preferences", {})
    user_message = state.get("user_message", "")

    # Build queries
    queries = build_search_queries(prefs, user_message)
    state["search_queries"] = queries

    # Execute searches
    results = await execute_web_search(queries)
    state["search_results"] = results

    return state
