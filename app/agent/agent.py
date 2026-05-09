import json
from collections.abc import AsyncIterator

from app.config import settings
from app.llm.client import chat_completion, chat_completion_stream
from app.agent.tools import TOOL_SCHEMAS, execute_tool, search_enabled

SYSTEM_PROMPT = """你是一个专业的旅行规划顾问。你的目标是为用户制定详细、实用、个性化的旅行计划。

## 工作方式

你采用**先研究、后规划**的两阶段工作法：

### 第一阶段：信息收集
当用户提出旅行需求时，先用 `web_search` 工具搜索最新的相关信息：
- 目的地概况、最佳旅行季节、当地特色
- 当前天气、住宿价格区间、热门景点
- 签证政策、货币汇率、交通方式
- 当地节日活动、美食推荐、安全提示

根据用户的具体需求调整搜索关键词。例如用户关注预算，就侧重搜索价格信息；用户喜欢美食，就搜索当地餐厅和夜市。

### 第二阶段：规划输出
收集到足够信息后，为用户生成一份结构化的旅行计划：

1. **目的地推荐** — 1-2句话说明为什么选这个目的地
2. **最佳出行时间** — 结合天气和季节
3. **每日行程** — 按天列出具体行程（上午/下午/晚上），附地点名称和简要说明
4. **预算估算** — 机票、住宿、餐饮、门票、交通的大致费用
5. **实用贴士** — 签证、货币、语言、交通、安全注意事项

## 重要原则

- **必须使用 web_search 获取最新信息**，不要仅凭训练数据。搜索查询用中文，每条查询具体明确。
- **一次搜索多个相关查询**（2-4个），提高效率。
- **支持对比**：如果用户没有明确目的地，搜索2-3个候选地做对比。
- **诚实透明**：如果搜索没找到某类信息，告知用户并给出基于常识的建议。
- **个性化**：始终围绕用户的预算、季节、兴趣偏好来规划。
- **预算敏感**：根据用户的预算等级推荐匹配的住宿和活动。
- **中国护照优先**：优先考虑中国公民免签或落地签的目的地。

## 输出风格

- 用自然、热情但不啰嗦的语言
- 避免冗长的表格，用清晰的条目式呈现
- 行程部分要具体，包含真实的地名和活动名称
- 费用用人民币（CNY）标注
- 如果用户后来追问或想调整，灵活修改计划"""

SYSTEM_PROMPT_NO_SEARCH = """你是一个专业的旅行规划顾问。你的目标是为用户制定详细、实用、个性化的旅行计划。

由于当前未配置网络搜索功能，请直接基于你的知识库为用户规划旅行。

## 输出格式

1. **目的地推荐** — 1-2句话说明为什么选这个目的地
2. **最佳出行时间** — 结合季节特点
3. **每日行程** — 按天列出具体行程（上午/下午/晚上），附推荐地点和简要说明
4. **预算估算** — 机票、住宿、餐饮、门票、交通的大致费用（人民币）
5. **实用贴士** — 签证、货币、语言、交通、安全注意事项

## 重要原则

- **个性化**：始终围绕用户的预算、季节、兴趣偏好来规划。
- **诚实透明**：对于不确定的实时信息（如具体价格、最新签证政策），请提醒用户自行核实。
- **中国护照优先**：优先考虑中国公民免签或落地签的目的地。
- 如果用户后来追问或想调整，灵活修改计划。"""


async def run(
    user_message: str,
    history: list[dict],
) -> AsyncIterator[dict]:
    has_search = search_enabled()
    prompt = SYSTEM_PROMPT if has_search else SYSTEM_PROMPT_NO_SEARCH
    tools = TOOL_SCHEMAS if has_search else None

    messages = [
        {"role": "system", "content": prompt},
        *history[-20:],
        {"role": "user", "content": user_message},
    ]

    # ---- Tool-calling loop (non-streaming, only when search is enabled) ----
    for _ in range(settings.max_tool_rounds if has_search else 0):
        response = await chat_completion(messages, tools=tools)

        tool_calls = response.get("tool_calls") or []
        if not tool_calls:
            messages.append(response)
            break

        messages.append(response)

        for tc in tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            tool_args = json.loads(func.get("arguments", "{}"))

            yield {
                "type": "tool_call",
                "name": tool_name,
                "args": tool_args,
            }

            result_str = execute_tool(tool_name, tool_args)

            try:
                result_obj = json.loads(result_str)
                if isinstance(result_obj, list):
                    preview = f"搜索完成，找到 {len(result_obj)} 组结果"
                elif isinstance(result_obj, dict) and "error" in result_obj:
                    preview = result_obj["error"]
                else:
                    preview = "搜索完成"
            except (json.JSONDecodeError, TypeError):
                preview = result_str[:100]

            yield {
                "type": "tool_result",
                "name": tool_name,
                "result_preview": preview,
            }

            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": result_str,
            })

    # ---- Final streaming response ----
    full_text = ""
    async for token in chat_completion_stream(messages):
        full_text += token
        yield {"type": "content", "content": token}

    yield {
        "type": "done",
        "full_text": full_text,
    }
