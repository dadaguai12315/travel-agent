from typing import TypedDict


class AgentState(TypedDict, total=False):
    """State object passed between nodes in the agent workflow."""

    # Identifiers
    session_id: str
    user_id: str

    # User input
    user_message: str
    conversation_history: list[dict]

    # Intent analysis
    intent: str  # "new_plan", "modify_plan", "chat"
    extracted_preferences: dict  # {budget, destination_type, season, interests, travelers, ...}

    # Research phase
    search_queries: list[str]
    search_results: list[dict]

    # Planning phase
    draft_plan: str
    plan_iteration: int  # How many times Planner has been called

    # Review phase
    review_passed: bool
    review_feedback: str  # If failed, what to fix

    # Final output
    final_response: str

    # Error tracking
    errors: list[str]

    # PPT pipeline
    travel_json: dict
    slide_dsl: list[dict]
    slide_theme: str
    visual_assets: list[dict]

    # Metadata
    iteration: int  # Total loop counter (prevents infinite loops)
    node_history: list[str]  # Track which nodes have been visited
