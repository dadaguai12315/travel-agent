"""
Reviewer Node

Validates the draft plan against user requirements.
Checks budget compliance, data accuracy, and completeness.
"""

from app.agent.state import AgentState


async def run_reviewer(state: AgentState) -> AgentState:
    """Review the draft plan for quality and budget compliance.

    In Phase 4, this will use LLM to critique the plan.
    For Phase 3, it does rule-based checks.
    """
    state["node_history"] = state.get("node_history", []) + ["reviewer"]

    draft = state.get("draft_plan", "")
    prefs = state.get("extracted_preferences", {})
    errors = []

    # Check 1: Plan is not empty
    if not draft or len(draft) < 100:
        errors.append("Plan is too short or empty")

    # Check 2: Budget compliance
    budget_amount = prefs.get("budget_amount", "")
    if budget_amount:
        import re
        match = re.search(r"人均\s*(\d+)\s*元", draft)
        if match:
            plan_per_person = int(match.group(1))
            budget_num = int(re.sub(r"[元块k千w万]", "", budget_amount))
            if "千" in budget_amount or "k" in budget_amount.lower():
                budget_num *= 1000
            if "万" in budget_amount or "w" in budget_amount.lower():
                budget_num *= 10000
            if plan_per_person > budget_num * 1.2:  # 20% tolerance
                errors.append(
                    f"预算超标：计划人均{plan_per_person}元，用户预算{budget_amount}"
                )

    # Check 3: Required sections present
    required_sections = ["行程概览", "每日行程", "费用明细", "行前清单", "贴士"]
    missing = [s for s in required_sections if s not in draft and s.lower() not in draft.lower()]
    if missing:
        errors.append(f"缺少章节：{', '.join(missing)}")

    # Check 4: Day-by-day structure
    if "Day 1" not in draft and "Day1" not in draft:
        errors.append("缺少每日行程结构")

    # Evaluate
    if errors:
        state["review_passed"] = False
        state["review_feedback"] = "\n".join(f"- {e}" for e in errors)
        state["errors"] = state.get("errors", []) + errors
    else:
        state["review_passed"] = True
        state["review_feedback"] = ""

    # Max review attempts (prevent infinite Planner→Reviewer loop)
    if state.get("plan_iteration", 0) >= 3:
        state["review_passed"] = True
        state["errors"] = state.get("errors", []) + ["Max review iterations reached, proceeding anyway"]

    return state
