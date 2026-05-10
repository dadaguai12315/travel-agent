from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_current_user


async def get_current_user_id(authorization: str = Header(...)) -> str:
    """Extract and validate JWT from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization header")
    token = authorization[7:]
    user_id = decode_access_token(token)
    if not user_id:
        raise UnauthorizedError("Invalid or expired token")
    return user_id


async def get_current_active_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the current authenticated User object."""
    return await get_current_user(db, user_id)
