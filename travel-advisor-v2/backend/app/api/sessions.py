from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.session import (
    SessionCreate,
    SessionDetail,
    SessionListResponse,
    SessionSummary,
    SessionUpdate,
)
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    sessions, total = await session_service.list_sessions(db, user_id, limit, offset)
    summaries = []
    for s in sessions:
        summaries.append(
            SessionSummary(
                id=s.id,
                title=s.title,
                status=s.status,
                msg_count=len(s.messages) if s.messages else 0,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
        )
    return SessionListResponse(sessions=summaries, total=total)


@router.post("", response_model=SessionSummary, status_code=201)
async def create_session(
    req: SessionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = await session_service.create_session(db, user_id, req.title)
    return SessionSummary(
        id=session.id,
        title=session.title,
        status=session.status,
        msg_count=0,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = await session_service.get_session(db, session_id, user_id)
    return SessionDetail(
        id=session.id,
        title=session.title,
        status=session.status,
        messages=[
            {"id": m.id, "role": m.role, "content": m.content, "token_count": m.token_count, "created_at": m.created_at}
            for m in (session.messages or [])
        ],
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.patch("/{session_id}", response_model=SessionSummary)
async def update_session(
    session_id: str,
    req: SessionUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = await session_service.update_session(
        db, session_id, user_id, req.title, req.status
    )
    return SessionSummary(
        id=session.id,
        title=session.title,
        status=session.status,
        msg_count=len(session.messages) if session.messages else 0,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await session_service.delete_session(db, session_id, user_id)
