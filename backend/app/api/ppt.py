"""
PPT Export Endpoint — POST /api/v1/ppt/generate

Accepts a session_id, retrieves the travel plan, runs the multi-agent
PPT pipeline, and returns a .pptx file download.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.ppt import generate_pptx
from app.services.session_service import get_session

router = APIRouter(prefix="/ppt", tags=["ppt"])


@router.post("/generate")
async def export_ppt(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate a .pptx presentation from a travel planning session."""
    # Load session
    session = await get_session(db, session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Extract the full assistant response (last assistant message)
    plan_text = ""
    for msg in reversed(session.messages or []):
        if msg.role == "assistant" and msg.content:
            plan_text = msg.content
            break

    if not plan_text:
        raise HTTPException(status_code=400, detail="No travel plan found in this session")

    # Run PPT pipeline
    pptx_bytes = await generate_pptx(plan_text)

    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="travel-plan.pptx"',
        },
    )
