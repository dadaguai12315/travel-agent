"""
Planner Node — LLM-powered travel plan generation.

Builds context from preferences and search results, then calls LLM
to generate a structured travel plan.
"""

from app.agent.state import AgentState
from app.core.llm_client import chat_completion, get_system_prompt


def _build_context(state: AgentState) -> str:
    """Build the user-facing context for the planner."""
    parts = []

    prefs = state.get("extracted_preferences", {})
    if prefs:
        parts.append(f"用户偏好：{prefs}")

    search_results = state.get("search_results", [])
    if search_results:
        parts.append("\n搜索到的实时信息：")
        for r in search_results:
            answer = r.get("answer", "")
            if answer:
                parts.append(f"- {r['query']}: {answer}")
            for s in r.get("sources", [])[:1]:
                parts.append(f"  [{s.get('title', '')}]({s.get('url', '')}): {s.get('content', '')[:200]}")

    feedback = state.get("review_feedback", "")
    if feedback:
        parts.append(f"\n⚠️ 上次计划的问题，请在本次修正：\n{feedback}")

    return "\n".join(parts)


async def run_planner(state: AgentState) -> AgentState:
    """Generate a travel plan using LLM with full context."""
    state["node_history"] = state.get("node_history", []) + ["planner"]
    state["plan_iteration"] = state.get("plan_iteration", 0) + 1

    user_message = state.get("user_message", "")
    context = _build_context(state)
    history = state.get("conversation_history", [])

    system_prompt = get_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        *history[-10:],
        {"role": "user", "content": f"用户需求：{user_message}\n\n参考资料：\n{context}\n\n请根据以上信息生成旅行计划。"},
    ]

    response = await chat_completion(messages)
    plan = response.get("content", "")
    state["draft_plan"] = plan
    return state
