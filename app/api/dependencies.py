from collections.abc import AsyncIterator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, try_current_context
from app.core.database import app_session
from app.modules.auth.model import User

# Swagger UI Bearer token security scheme
http_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Provide database session with auto-commit on success and rollback on error."""
    async with app_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_authenticated_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> RequestContext:
    """Get authenticated context from request scope."""
    ctx = try_current_context()
    if ctx is None or ctx.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ctx


async def get_current_user(
    context: RequestContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Retrieve current user from database."""
    result = await db.scalar(select(User).where(User.id == context.user_id))
    if result is None or not result.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result
