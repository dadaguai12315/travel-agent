import json
from collections.abc import AsyncIterator

from app.config import settings
from app.llm.client import chat_completion, chat_completion_stream
from app.agent.tools import TOOL_SCHEMAS, execute_tool

SYSTEM_PROMPT = """你是一个专业的旅行顾问助手。你的任务是根据用户的偏好为他们推荐旅行目的地和行程建议。

## 工作原则
1. **先收集数据再推荐**：在给出任何推荐之前，先使用工具查询具体数据。
2. **多维对比**：如果用户犹豫不决，可以查询多个目的地进行对比分析。
3. **诚实告知**：如果工具返回空结果，诚实地告诉用户并建议扩大搜索范围。
4. **结构化呈现**：用清晰的结构展示信息，包括费用估算、最佳季节和实用贴士。
5. **预算意识**：始终关注用户的预算偏好并给出匹配的推荐。
6. **个性化**：根据用户的兴趣标签（海滩/文化/美食/冒险/自然/购物）定制推荐。

## 回复格式
- 先用简洁的语言总结推荐方案
- 再用结构化方式列出每个推荐目的地的详细信息
- 最后提供实用建议（签证、货币、交通等）

## 注意
- 永远不要编造酒店名称、价格或天气数据——请使用工具查询。
- 如果用户没有指定预算，默认假设为中等预算。
- 中国用户不需要签证的目的地可以优先推荐。"""


async def run(
    user_message: str,
    history: list[dict],
) -> AsyncIterator[dict]:
    """
    Agent loop: tool-calling rounds (non-streaming) + final response (streaming).

    Yields SSE event dicts:
      {"type": "tool_call", "name": str, "args": dict}
      {"type": "tool_result", "name": str, "result_preview": str}
      {"type": "content", "content": str}
      {"type": "done"}
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history[-20:],  # Keep last 20 messages
        {"role": "user", "content": user_message},
    ]

    # ---- Tool-calling loop (non-streaming) ----
    for round_num in range(settings.max_tool_rounds):
        response = await chat_completion(messages, tools=TOOL_SCHEMAS)

        tool_calls = response.get("tool_calls") or []
        if not tool_calls:
            # No tool calls → append assistant message and break
            messages.append(response)
            break

        # Append assistant message with tool calls
        messages.append(response)

        for tc in tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            tool_args = json.loads(func.get("arguments", "{}"))

            # Notify frontend: tool call started
            yield {
                "type": "tool_call",
                "name": tool_name,
                "args": tool_args,
            }

            # Execute tool
            result_str = execute_tool(tool_name, tool_args)

            # Build a result preview for the frontend
            try:
                result_obj = json.loads(result_str)
                if isinstance(result_obj, list):
                    preview = f"找到 {len(result_obj)} 条结果"
                elif isinstance(result_obj, dict) and "error" in result_obj:
                    preview = result_obj["error"]
                else:
                    preview = "查询完成"
            except (json.JSONDecodeError, TypeError):
                preview = result_str[:100]

            yield {
                "type": "tool_result",
                "name": tool_name,
                "result_preview": preview,
            }

            # Append tool result to conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": result_str,
            })
    else:
        # Max rounds reached → force final response
        pass

    # ---- Final streaming response ----
    full_text = ""
    async for token in chat_completion_stream(messages):
        full_text += token
        yield {"type": "content", "content": token}

    yield {
        "type": "done",
        "full_text": full_text,
    }
