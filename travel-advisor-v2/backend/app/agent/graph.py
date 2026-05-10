"""
State Graph Controller

Orchestrates the multi-node agent workflow with LLM-powered streaming.

Workflow:
    START → Analyzer → [route]
      ├─ "new_plan" → Research → Plan & Stream → END
      ├─ "modify_plan" → Plan & Stream → END
      └─ "chat" → Quick Stream → END
"""

from collections.abc import AsyncIterator

from app.agent.nodes.analyzer import run_analyzer
from app.agent.nodes.planner import _build_context
from app.agent.nodes.researcher import run_researcher
from app.agent.nodes.reviewer import run_reviewer
from app.agent.state import AgentState
from app.core.llm_client import chat_completion_stream, get_system_prompt
from app.core.llm_prompts import SYSTEM_PROMPT_NO_SEARCH


async def run_workflow_stream(
    session_id: str,
    user_id: str,
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> AsyncIterator[dict]:
    """Execute agent workflow and yield SSE events.

    Phase 4: real LLM calls throughout. Streaming final response via SSE.
    """
    history = conversation_history or []

    state: AgentState = {
        "session_id": session_id,
        "user_id": user_id,
        "user_message": user_message,
        "conversation_history": history,
        "intent": "",
        "extracted_preferences": {},
        "search_queries": [],
        "search_results": [],
        "draft_plan": "",
        "plan_iteration": 0,
        "review_passed": False,
        "review_feedback": "",
        "final_response": "",
        "errors": [],
        "iteration": 0,
        "node_history": [],
    }

    # Step 1: Analyze intent (LLM, non-streaming)
    yield {"event": "status", "data": {"msg": "正在分析您的需求..."}}
    state = await run_analyzer(state)
    intent = state.get("intent", "new_plan")

    if intent == "chat":
        # Simple chat: stream quick LLM response
        yield {"event": "status", "data": {"msg": ""}}
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_NO_SEARCH},
            *history[-6:],
            {"role": "user", "content": user_message},
        ]
        async for token in chat_completion_stream(messages):
            yield {"event": "content", "data": {"text": token}}
        yield {"event": "done", "data": {"usage": {"tokens": 0}}}
        return

    # Step 2: Research (Tavily web search)
    if intent == "new_plan":
        yield {"event": "status", "data": {"msg": "正在搜索最新旅行信息..."}}
        state = await run_researcher(state)
        for q in state.get("search_queries", []):
            yield {"event": "tool_call", "data": {"tool": "web_search", "query": q}}

    # Step 3: Build context and stream the plan
    yield {"event": "status", "data": {"msg": "正在生成旅行计划..."}}

    # Generate plan via non-streaming first (for review)
    from app.agent.nodes.planner import run_planner

    state = await run_planner(state)
    state = await run_reviewer(state)

    # Retry if review failed (up to 2 times)
    retries = 0
    while not state.get("review_passed") and retries < 2:
        yield {"event": "status", "data": {"msg": f"正在优化计划...（第{retries+1}次调整）"}}
        state = await run_planner(state)
        state = await run_reviewer(state)
        retries += 1

    # Step 4: Stream the final plan
    plan = state.get("draft_plan", "")

    if plan:
        # Send plan in chunks for a streaming feel
        chunk_size = 50
        for i in range(0, len(plan), chunk_size):
            yield {
                "event": "content",
                "data": {"text": plan[i : i + chunk_size]},
            }

    yield {"event": "done", "data": {"usage": {"tokens": 0}}}
