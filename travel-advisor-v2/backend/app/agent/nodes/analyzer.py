"""
Intent Analyzer Node

Identifies the user's intent and extracts structured preferences
from their message. Routes to appropriate downstream nodes.
"""

from app.agent.state import AgentState

# Intent classification keywords
INTENT_PATTERNS = {
    "new_plan": [
        "推荐", "想去", "计划", "规划", "安排", "旅行", "旅游",
        "度假", "攻略", "行程", "去哪里", "目的地", "帮我",
    ],
    "modify_plan": [
        "太贵", "便宜", "换", "改", "调整", "不要", "换个",
        "多加", "减少", "延长", "缩短", "还有别的", "备选",
    ],
}


def extract_preferences(message: str) -> dict:
    """Simple preference extraction. Will be enhanced with LLM in Phase 4."""
    prefs = {}
    msg_lower = message.lower()

    # Budget detection
    if any(w in msg_lower for w in ["穷游", "省钱", "便宜", "经济", "预算有限"]):
        prefs["budget"] = "经济"
    elif any(w in msg_lower for w in ["奢华", "高端", "五星", "豪华", "蜜月"]):
        prefs["budget"] = "奢华"
    elif any(w in msg_lower for w in ["中等", "舒适", "性价比"]):
        prefs["budget"] = "中等"

    # Extract numeric budget
    import re
    budget_match = re.search(r"(\d+)\s*(元|块|k|千|万)", message)
    if budget_match:
        prefs["budget_amount"] = budget_match.group(1) + budget_match.group(2)

    # Destination type
    if any(w in msg_lower for w in ["海滩", "海边", "海岛", "沙滩", "潜水"]):
        prefs["destination_type"] = "海滩"
    elif any(w in msg_lower for w in ["古城", "文化", "历史", "古迹", "博物馆"]):
        prefs["destination_type"] = "文化古城"
    elif any(w in msg_lower for w in ["自然", "山", "徒步", "森林", "湖"]):
        prefs["destination_type"] = "自然风光"
    elif any(w in msg_lower for w in ["都市", "城市", "购物", "美食"]):
        prefs["destination_type"] = "都市"

    # Season
    if any(w in msg_lower for w in ["避暑", "凉快", "夏天", "夏季", "7月", "8月"]):
        prefs["season"] = "夏季避暑"
    elif any(w in msg_lower for w in ["冬天", "冬季", "12月", "1月", "温暖"]):
        prefs["season"] = "冬季避寒"

    # Travelers
    if any(w in msg_lower for w in ["情侣", "蜜月", "二人", "2人"]):
        prefs["travelers"] = "情侣"
    elif any(w in msg_lower for w in ["家庭", "孩子", "亲子"]):
        prefs["travelers"] = "家庭"
    elif any(w in msg_lower for w in ["朋友", "结伴", "多人"]):
        prefs["travelers"] = "朋友结伴"
    elif any(w in msg_lower for w in ["独自", "一个人", "solo"]):
        prefs["travelers"] = "独自"

    # Region constraint
    if any(w in msg_lower for w in ["国内", "中国", "国内游"]):
        prefs["region"] = "中国"
    elif any(w in msg_lower for w in ["出国", "国外", "东南亚", "日本", "欧洲"]):
        prefs["region"] = "海外"

    return prefs


async def run_analyzer(state: AgentState) -> AgentState:
    """Analyze user intent and extract preferences.

    In Phase 3, this uses keyword matching as mock logic.
    In Phase 4, this will call the LLM for accurate intent classification.
    """
    message = state.get("user_message", "")
    state["node_history"] = state.get("node_history", []) + ["analyzer"]

    # Classify intent
    intent = "chat"  # default: casual chat
    for intent_name, keywords in INTENT_PATTERNS.items():
        if any(kw in message for kw in keywords):
            intent = intent_name
            break

    state["intent"] = intent
    state["extracted_preferences"] = extract_preferences(message)
    state["iteration"] = state.get("iteration", 0)

    return state
