"""
State Graph Controller

Orchestrates the multi-node agent workflow as a finite state machine.

Workflow:
    START → Analyzer → [route by intent]
      ├─ "new_plan" → Researcher → Planner → Reviewer → [route by review]
      │                                                   ├─ passed → Streamer → END
      │                                                   └─ failed → Planner (retry)
      ├─ "modify_plan" → Planner → Reviewer → Streamer → END
      └─ "chat" → Streamer → END
"""

from collections.abc import AsyncIterator

from app.agent.nodes.analyzer import run_analyzer
from app.agent.nodes.planner import run_planner
from app.agent.nodes.researcher import run_researcher
from app.agent.nodes.reviewer import run_reviewer
from app.agent.nodes.streamer import run_streamer
from app.agent.state import AgentState

# Maximum total iterations before forced termination
MAX_ITERATIONS = 10


def route_after_analyzer(state: AgentState) -> str:
    """Decide next node based on intent analysis."""
    intent = state.get("intent", "chat")
    if intent == "new_plan":
        return "researcher"
    elif intent == "modify_plan":
        return "planner"
    else:
        return "streamer"


def route_after_reviewer(state: AgentState) -> str:
    """Decide: accept plan → stream, or reject → re-plan."""
    if state.get("review_passed", False):
        return "streamer"
    else:
        return "planner"


# Node runner registry
NODE_RUNNERS = {
    "analyzer": run_analyzer,
    "researcher": run_researcher,
    "planner": run_planner,
    "reviewer": run_reviewer,
    "streamer": run_streamer,
}

# Routing functions
ROUTERS = {
    "analyzer": route_after_analyzer,
    "reviewer": route_after_reviewer,
}


async def run_workflow(state: AgentState) -> AgentState:
    """Execute the full agent workflow.

    Returns the final state with final_response populated.
    """
    state["iteration"] = 0
    state["errors"] = []
    state["node_history"] = []

    # Start with analyzer
    current_node = "analyzer"

    while state["iteration"] < MAX_ITERATIONS:
        state["iteration"] += 1

        # Run current node
        runner = NODE_RUNNERS.get(current_node)
        if not runner:
            state["errors"].append(f"Unknown node: {current_node}")
            break

        state = await runner(state)

        # Terminal node
        if current_node == "streamer":
            break

        # Route to next node
        router = ROUTERS.get(current_node)
        if router:
            next_node = router(state)
        else:
            # Linear flow: researcher → planner, planner → reviewer
            if current_node == "researcher":
                next_node = "planner"
            elif current_node == "planner":
                next_node = "reviewer"
            else:
                next_node = "streamer"

        current_node = next_node

    # Ensure we always have a response
    if not state.get("final_response"):
        state["final_response"] = "抱歉，处理您的请求时遇到了问题，请重试。"

    return state


async def run_workflow_stream(
    session_id: str,
    user_id: str,
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> AsyncIterator[dict]:
    """Execute workflow and yield SSE events for streaming.

    Yields:
        {"event": "status", "data": {"msg": "..."}}
        {"event": "tool_call", "data": {"tool": "...", "query": "..."}}
        {"event": "content", "data": {"text": "..."}}
        {"event": "error", "data": {"code": 500, "msg": "..."}}
        {"event": "done", "data": {"usage": {...}}}
    """
    state: AgentState = {
        "session_id": session_id,
        "user_id": user_id,
        "user_message": user_message,
        "conversation_history": conversation_history or [],
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

    try:
        # Run analyzer
        yield {"event": "status", "data": {"msg": "正在分析您的需求..."}}
        state = await run_analyzer(state)
        intent = state.get("intent", "chat")

        if intent == "new_plan":
            # Research
            yield {"event": "status", "data": {"msg": "正在搜索最新旅行信息..."}}
            state = await run_researcher(state)

            # Yield tool calls for frontend
            for q in state.get("search_queries", []):
                yield {"event": "tool_call", "data": {"tool": "web_search", "query": q}}

            # Plan
            yield {"event": "status", "data": {"msg": "正在生成旅行计划..."}}
            state = await run_planner(state)

            # Review
            yield {"event": "status", "data": {"msg": "正在审核计划..."}}
            state = await run_reviewer(state)

            # Re-plan if needed (up to 2 retries)
            while not state.get("review_passed") and state.get("plan_iteration", 0) < 3:
                yield {"event": "status", "data": {"msg": "正在优化计划..."}}
                state = await run_planner(state)
                state = await run_reviewer(state)

        elif intent == "modify_plan":
            yield {"event": "status", "data": {"msg": "正在调整您的计划..."}}
            state = await run_planner(state)
            state = await run_reviewer(state)

        # Stream final response
        response = state.get("final_response", "")
        yield {"event": "status", "data": {"msg": "完成！"}}

        # In Phase 4, this will stream token-by-token via LLM
        # For Phase 3, we send the entire mock response
        if response:
            yield {"event": "content", "data": {"text": response}}

        yield {
            "event": "done",
            "data": {"usage": {"tokens": 0}, "node_history": state.get("node_history", [])},
        }

    except Exception as e:
        yield {"event": "error", "data": {"code": 500, "msg": str(e)}}
