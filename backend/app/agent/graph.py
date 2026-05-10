"""
State Graph Controller — Streaming-First Architecture

Workflow:
    START → Analyzer → [Research if needed] → Stream Plan (token-by-token) → END

The final response is streamed directly from the LLM via SSE, so the user
sees content immediately, like ChatGPT.
"""

from collections.abc import AsyncIterator

from app.agent.nodes.analyzer import run_analyzer
from app.agent.nodes.planner import _build_context
from app.agent.nodes.researcher import run_researcher
from app.agent.state import AgentState
from app.core.llm_client import chat_completion_stream
from app.core.llm_prompts import SYSTEM_PROMPT_WITH_SEARCH, SYSTEM_PROMPT_NO_SEARCH
from app.agent.tools import search_enabled


def _build_stream_messages(state: AgentState) -> list[dict]:
    """Build the message list for the final streaming LLM call."""
    user_message = state.get("user_message", "")
    context = _build_context(state)
    history = state.get("conversation_history", [])

    system = SYSTEM_PROMPT_WITH_SEARCH if search_enabled() else SYSTEM_PROMPT_NO_SEARCH

    return [
        {"role": "system", "content": system},
        *history[-10:],
        {"role": "user", "content": f"{user_message}\n\n参考资料：\n{context}" if context else user_message},
    ]


async def run_workflow_stream(
    session_id: str,
    user_id: str,
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> AsyncIterator[dict]:
    """Execute agent workflow and stream final response token-by-token."""
    history = conversation_history or []

    state: AgentState = {
        "session_id": session_id,
        "user_id": user_id,
        "user_message": user_message,
        "conversation_history": history,
        "intent": "new_plan",
        "extracted_preferences": {},
        "search_queries": [],
        "search_results": [],
        "draft_plan": "",
        "plan_iteration": 0,
        "review_passed": True,
        "review_feedback": "",
        "final_response": "",
        "errors": [],
        "iteration": 0,
        "node_history": [],
    }

    # Step 1: Analyze intent (fast, ~1s)
    yield {"event": "status", "data": {"msg": "正在分析需求..."}}
    state = await run_analyzer(state)
    intent = state.get("intent", "new_plan")

    if intent == "chat":
        yield {"event": "status", "data": {"msg": ""}}
        messages = _build_stream_messages(state)
        async for token in chat_completion_stream(messages):
            yield {"event": "content", "data": {"text": token}}
        yield {"event": "done", "data": {}}
        return

    # Step 2: Research (optional, shows progress)
    if intent == "new_plan" and search_enabled():
        yield {"event": "status", "data": {"msg": "正在搜索最新信息..."}}
        state = await run_researcher(state)
        for q in state.get("search_queries", []):
            yield {"event": "tool_call", "data": {"tool": "web_search", "query": q}}

    # Step 3: Stream the plan directly from LLM (token-by-token)
    yield {"event": "status", "data": {"msg": ""}}
    messages = _build_stream_messages(state)

    async for token in chat_completion_stream(messages):
        yield {"event": "content", "data": {"text": token}}

    yield {"event": "done", "data": {}}
