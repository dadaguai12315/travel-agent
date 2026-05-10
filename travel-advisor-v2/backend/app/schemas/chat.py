from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, description="Session ID. Creates new session if None.")
    message: str = Field(min_length=1, max_length=10000)
    stream: bool = Field(default=True)


class SSEEvent(BaseModel):
    event: str  # "status", "tool_call", "content", "error", "done"
    data: dict
