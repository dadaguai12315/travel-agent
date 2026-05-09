import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from app.agent.agent import run
from app.memory import session as memory

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@router.get("/api/sessions")
async def list_sessions():
    """Return all active sessions with metadata."""
    return JSONResponse(memory.list_sessions())


@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Return session with full history."""
    session = memory.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return JSONResponse(session)


@router.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if not memory.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return JSONResponse({"ok": True})


@router.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    session_id = req.session_id or memory.create_session()
    history = memory.get_history(session_id)

    # Save user message immediately (before streaming starts)
    memory.add_message(session_id, "user", req.message)

    async def event_stream():
        full_text = ""
        async for event in run(req.message, history):
            if event["type"] == "content":
                full_text += event["content"]
            elif event["type"] == "done":
                full_text = event.get("full_text", full_text)
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        # Save assistant response after streaming completes
        if full_text:
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
