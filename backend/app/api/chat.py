"""
Chat SSE Endpoint — POST /api/v1/chat/stream

Accepts user messages, runs the agent workflow, streams results via SSE.
Persists messages to PostgreSQL before and after the stream.
"""

import json
import logging
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_workflow_stream
from app.api.deps import get_current_user_id
from app.db.session import async_session_factory, get_db
from app.schemas.chat import ChatRequest
from app.services.session_service import add_message as save_message
from app.services.session_service import create_session, get_session

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def _format_sse(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Create or reuse session (in endpoint context)
    if req.session_id:
        await get_session(db, req.session_id, user_id)
        session_id = req.session_id
    else:
        session = await create_session(db, user_id)
        session_id = session.id

    # Save user message (in endpoint context)
    await save_message(db, session_id, user_id, "user", req.message)

    # Load history (in endpoint context)
    session = await get_session(db, session_id, user_id)
    history = [
        {"role": m.role, "content": m.content}
        for m in (session.messages or [])
    ]

    async def event_stream():
        start_time = time.time()
        full_response = ""

        try:
            async for sse_event in run_workflow_stream(
                session_id=session_id,
                user_id=user_id,
                user_message=req.message,
                conversation_history=history,
            ):
                event_type = sse_event.get("event", "content")
                data = sse_event.get("data", {})

                if event_type == "content":
                    full_response += data.get("text", "")

                yield _format_sse(event_type, data)

        except Exception as e:
            logger.exception("Chat stream failed for session %s", session_id)
            yield _format_sse("error", {"code": 500, "msg": str(e)})

        finally:
            # Use a fresh DB session inside the generator context
            if full_response:
                async with async_session_factory() as stream_db:
                    await save_message(
                        stream_db, session_id, user_id, "assistant", full_response
                    )

            elapsed = time.time() - start_time
            yield _format_sse("done", {
                "session_id": session_id,
                "usage": {"elapsed_seconds": round(elapsed, 1)},
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Session-Id": session_id,
        },
    )
