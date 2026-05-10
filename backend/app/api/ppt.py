"""
PPT Export — SSE progress + download.

Streams progress events during generation, then provides a download URL.
"""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.ppt.pipeline import generate_pptx_stream
from app.services.session_service import get_session

router = APIRouter(prefix="/ppt", tags=["ppt"])

# In-memory store for generated files (TTL: 5 min)
_file_store: dict[str, bytes] = {}


@router.post("/generate")
async def export_ppt_progress(
    session_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate PPT with SSE progress events. Download via /ppt/download/{token}."""
    session = await get_session(db, session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    plan_text = ""
    for msg in reversed(session.messages or []):
        if msg.role == "assistant" and msg.content:
            plan_text = msg.content
            break

    if not plan_text:
        raise HTTPException(status_code=400, detail="No travel plan found")

    download_token = uuid.uuid4().hex[:16]

    async def event_stream():
        try:
            async for event in generate_pptx_stream(plan_text):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            # Generate and store the final file
            pptx_bytes = await _build_pptx(plan_text)
            _file_store[download_token] = pptx_bytes
            yield f"data: {json.dumps({'type': 'done', 'token': download_token}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'msg': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/download/{token}")
async def download_ppt(token: str):
    """Download a previously generated PPT file by token."""
    data = _file_store.pop(token, None)
    if not data:
        raise HTTPException(status_code=404, detail="File not found or expired")
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": 'attachment; filename="travel-plan.pptx"'},
    )


async def _build_pptx(plan_text: str) -> bytes:
    """Build PPTX without streaming (for final output)."""
    from app.ppt.pipeline import generate_pptx
    return await generate_pptx(plan_text)
