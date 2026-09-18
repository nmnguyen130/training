from collections.abc import Callable
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.core.exceptions import ServiceError
from app.modules.auth.model import UserAccount
from app.modules.rbac.controller import RbacController


def require_permission(permission_code: str) -> Callable:
    async def dependency(
        current_user: UserAccount = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> UserAccount:
        controller = RbacController(db)
        allowed = await controller.has_permission(current_user.user_id, permission_code)
        if not allowed:
            raise ServiceError.forbidden(f"Permission denied: requires '{permission_code}'")
        return current_user

    return dependency
