from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.message import Message
from app.models.session import Session


async def create_session(db: AsyncSession, user_id: str, title: str = "New Trip") -> Session:
    session = Session(user_id=user_id, title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(
    db: AsyncSession, user_id: str, limit: int = 20, offset: int = 0
) -> tuple[list[Session], int]:
    """Return (sessions, total_count) for a user."""
    base_query = select(Session).where(
        Session.user_id == user_id, Session.status != "deleted"
    )

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    sessions_query = (
        base_query
        .order_by(Session.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    sessions = (await db.execute(sessions_query)).scalars().all()

    return list(sessions), total


async def get_session(db: AsyncSession, session_id: str, user_id: str) -> Session:
    result = await db.execute(
        select(Session)
        .where(Session.id == session_id, Session.user_id == user_id)
        .options(selectinload(Session.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError("Session", session_id)
    return session


async def update_session(
    db: AsyncSession, session_id: str, user_id: str, title: str | None = None, status: str | None = None
) -> Session:
    session = await get_session(db, session_id, user_id)
    if title is not None:
        session.title = title
    if status is not None:
        session.status = status
    await db.commit()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session_id: str, user_id: str) -> None:
    session = await get_session(db, session_id, user_id)
    session.status = "deleted"
    await db.commit()


async def add_message(
    db: AsyncSession, session_id: str, user_id: str, role: str, content: str, token_count: int = 0
) -> Message:
    # Verify session belongs to user
    await get_session(db, session_id, user_id)
    msg = Message(session_id=session_id, role=role, content=content, token_count=token_count)
    db.add(msg)
    # Touch session updated_at
    await db.execute(
        select(Session).where(Session.id == session_id)
    )
    await db.commit()
    await db.refresh(msg)
    return msg
