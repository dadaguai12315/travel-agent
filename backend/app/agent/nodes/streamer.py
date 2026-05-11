"""
Streamer Node

Prepares the final response and yields SSE events.
This is the terminal node in the workflow.
"""

from app.agent.state import AgentState


async def run_streamer(state: AgentState) -> AgentState:
    """Prepare final response for SSE streaming.

    In Phase 4, this will yield actual SSE events.
    For Phase 3, it stores the final response in state.
    """
    state["node_history"] = state.get("node_history", []) + ["streamer"]

    intent = state.get("intent", "chat")

    if intent == "new_plan" or intent == "modify_plan":
        state["final_response"] = state.get("draft_plan", "No plan generated.")
    elif intent == "chat":
        state["final_response"] = (
            "你好！我是 Travel Advisor。\n\n"
            "我可以帮你：\n"
            "- 规划详细的旅行行程\n"
            "- 根据预算推荐目的地\n"
            "- 调整已有计划\n\n"
            "请告诉我你的旅行需求！"
        )
    else:
        state["final_response"] = state.get("draft_plan", "")

    return state
