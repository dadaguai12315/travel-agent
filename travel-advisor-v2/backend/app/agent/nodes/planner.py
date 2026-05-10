"""
Planner Node

Generates a structured travel plan in Markdown format using
user preferences and search results as context.

In Phase 3, this generates a mock plan from templates.
In Phase 4, this will call the LLM with full context.
"""

from app.agent.state import AgentState


def _build_plan_context(state: AgentState) -> str:
    """Build context string for the planner from current state."""
    prefs = state.get("extracted_preferences", {})
    search = state.get("search_results", [])
    feedback = state.get("review_feedback", "")

    ctx = f"User preferences: {prefs}\n"

    if search:
        ctx += "\nSearch results:\n"
        for r in search:
            if "answer" in r and r["answer"]:
                ctx += f"- {r['query']}: {r['answer'][:200]}\n"

    if feedback:
        ctx += f"\nReview feedback to address: {feedback}\n"

    return ctx


# Mock plan templates for Phase 3 testing
MOCK_PLAN_TEMPLATE = """### 📍 行程概览
{intro}

### 🗺️ 每日行程

**Day 1 — 抵达 + 初探**
- **上午 (08:00-12:00)**：{d1_morning}
- **中午 (12:00-14:00)**：{d1_lunch}
- **下午 (14:00-18:00)**：{d1_afternoon}
- **晚上 (18:00-22:00)**：{d1_evening}

**Day 2 — 核心体验**
- **上午 (08:00-12:00)**：{d2_morning}
- **中午 (12:00-14:00)**：{d2_lunch}
- **下午 (14:00-18:00)**：{d2_afternoon}
- **晚上 (18:00-22:00)**：{d2_evening}

**Day 3 — 深度探索**
- **上午 (08:00-12:00)**：{d3_morning}
- **中午 (12:00-14:00)**：{d3_lunch}
- **下午 (14:00-18:00)**：{d3_afternoon}
- **晚上 (18:00-22:00)**：{d3_evening}

### 💰 费用明细

| 类别 | 明细 | 单价(元) | 数量 | 小计(元) |
|------|------|----------|------|----------|
| 大交通 | {transport_detail} | {transport_cost} | 2人 | {transport_total} |
| 住宿 | {hotel_detail} | {hotel_cost} | {nights}晚 | {hotel_total} |
| 门票 | 各景点门票 | {ticket_cost} | 2人 | {ticket_total} |
| 餐饮 | 三餐+小吃 | 150 | {days}天 | {food_total} |
| 市内交通 | 打车/公交 | 60 | {days}天 | {local_transport} |
| **合计** | | | | **{total}** |

**人均 {per_person} 元**

### 📋 行前清单
- 证件类：身份证
- 衣物类：根据季节准备
- 其他：充电宝、防晒、常用药品

### 💡 贴士
- {tip1}
- {tip2}
{review_note}
"""


async def run_planner(state: AgentState) -> AgentState:
    """Generate a travel plan.

    In Phase 4, this will call the LLM with context.
    For Phase 3, it fills a mock template.
    """
    state["node_history"] = state.get("node_history", []) + ["planner"]
    state["plan_iteration"] = state.get("plan_iteration", 0) + 1

    prefs = state.get("extracted_preferences", {})
    dest_type = prefs.get("destination_type", "综合")
    budget = prefs.get("budget", "中等")
    review_feedback = state.get("review_feedback", "")

    days = 3  # Default
    per_day = 500 if budget == "经济" else 800 if budget == "中等" else 1500
    total = per_day * days
    per_person = total // 2

    plan = MOCK_PLAN_TEMPLATE.format(
        intro=f"为您推荐的{dest_type}主题 {days}天{days-1}晚行程，预算{per_person}元/人。",
        d1_morning="出发前往目的地，入住酒店",
        d1_lunch="品尝当地特色美食 (人均60元)",
        d1_afternoon="游览核心景点，感受当地风光 (3小时)",
        d1_evening="漫步夜市或老街，晚餐 (人均80元)",
        d2_morning="早起深度游览经典景区 (4小时)",
        d2_lunch="景区附近简餐 (人均40元)",
        d2_afternoon="体验特色活动或小众景点 (3小时)",
        d2_evening="当地特色餐厅晚餐，欣赏夜景 (人均100元)",
        d3_morning="自由探索，购买伴手礼",
        d3_lunch="离开前最后一顿当地美食 (人均60元)",
        d3_afternoon="退房，前往车站/机场，返程",
        d3_evening="抵达家中",
        transport_detail="往返火车票/机票",
        transport_cost=400 if budget == "经济" else 800,
        transport_total=800 if budget == "经济" else 1600,
        hotel_detail=f"{'经济型' if budget == '经济' else '舒适型'}酒店",
        hotel_cost=150 if budget == "经济" else 300,
        nights=days - 1,
        hotel_total=150 * (days - 1) if budget == "经济" else 300 * (days - 1),
        ticket_cost=100 if budget == "经济" else 200,
        ticket_total=200 if budget == "经济" else 400,
        days=days,
        food_total=150 * days,
        local_transport=60 * days,
        total=total,
        per_person=per_person,
        tip1="提前网上订票可节省20-30%费用",
        tip2="避开周末和节假日出行，住宿价格更低",
        review_note=f"\n> ⚠️ 注意：以上为 Mock 数据（Phase 3）。Phase 4 接入 LLM 后将生成真实计划。\n{review_feedback}" if review_feedback else f"\n> ⚠️ Mock 数据（Phase 3），Phase 4 接入 LLM 生成真实计划。",
    )

    state["draft_plan"] = plan
    return state
