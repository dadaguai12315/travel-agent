import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.agent import run
from app.memory import session as memory

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@router.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    session_id = req.session_id or memory.create_session()
    history = memory.get_history(session_id)

    async def event_stream():
        full_text = ""
        async for event in run(req.message, history):
            if event["type"] == "content":
                full_text += event["content"]
            elif event["type"] == "done":
                full_text = event.get("full_text", full_text)
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        # Save conversation after completion
        memory.add_message(session_id, "user", req.message)
        memory.add_message(session_id, "assistant", full_text)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Session-Id": session_id,
        },
    )
