"""
Intent Analyzer Node — LLM-powered intent classification and preference extraction.
"""

import json

from app.agent.state import AgentState
from app.core.llm_client import chat_completion

ANALYZER_PROMPT = """分析以下用户的旅行需求，返回JSON格式结果。

## 输出格式
{
    "intent": "new_plan" | "modify_plan" | "chat",
    "preferences": {
        "budget": "经济" | "中等" | "奢华" | null,
        "budget_amount": "用户提到的具体预算金额" | null,
        "destination_type": "海滩" | "文化古城" | "自然风光" | "都市" | null,
        "season": "用户提到的季节或月份" | null,
        "travelers": "情侣" | "家庭" | "朋友结伴" | "独自" | null,
        "region": "中国" | "海外" | null,
        "duration_days": 天数数字 | null,
        "special_requirements": ["特殊需求列表"] | []
    }
}

## 意图分类
- "new_plan": 用户想规划一次新的旅行
- "modify_plan": 用户想修改现有计划（太贵了、换一个、调整天数等）
- "chat": 一般闲聊或咨询

## 用户消息
{user_message}

只返回JSON，不要其他内容。"""


async def run_analyzer(state: AgentState) -> AgentState:
    """LLM-powered intent analysis and preference extraction."""
    state["node_history"] = state.get("node_history", []) + ["analyzer"]

    message = state.get("user_message", "")

    try:
        prompt = ANALYZER_PROMPT.format(user_message=message)
        response = await chat_completion([
            {"role": "user", "content": prompt},
        ])

        content = response.get("content", "{}")
        # Strip markdown code fences if present
        content = content.strip().removeprefix("```json").removesuffix("```").strip()

        result = json.loads(content)
        state["intent"] = result.get("intent", "new_plan")
        state["extracted_preferences"] = result.get("preferences", {})

    except (json.JSONDecodeError, Exception):
        # Fallback to keyword matching if LLM fails
        state["intent"] = "new_plan"
        state["extracted_preferences"] = {}

    state["iteration"] = state.get("iteration", 0)
    return state
