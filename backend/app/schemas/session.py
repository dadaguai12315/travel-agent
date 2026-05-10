from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: str = Field(default="New Trip", max_length=100)


class SessionUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=100)
    status: str | None = None  # "active", "archived", "deleted"


class SessionSummary(BaseModel):
    id: str
    title: str
    status: str
    msg_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    token_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionDetail(BaseModel):
    id: str
    title: str
    status: str
    messages: list[MessageOut]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]
    total: int
