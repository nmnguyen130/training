from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.auth.controller import AuthController
from app.modules.auth.model import UserAccount
from app.modules.auth.schemas import (
    PasswordChange,
    TokenRefresh,
    TokenResponse,
    UserAccountResponse,
    UserAccountUpdate,
    UserCreate,
    UserLogin,
)
from app.modules.rbac.dependencies import require_permission
from app.utils.pagination import PaginatedResponse, PaginationParams, paginate

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
users_router = APIRouter(prefix="/users", tags=["Users"])


def get_auth_controller(db: AsyncSession = Depends(get_db)) -> AuthController:
    return AuthController(db)


# Auth Endpoints
@auth_router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.login(data)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: TokenRefresh,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.refresh_token(data.refresh_token)


# Users Endpoints
@users_router.post(
    "",
    response_model=UserAccountResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("user.create"))],
)
async def create_user(
    data: UserCreate,
    current_user: UserAccount = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.create_user(data, assigned_by=current_user.user_id)


@users_router.get("/me", response_model=UserAccountResponse)
async def get_me(
    current_user: UserAccount = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.get_by_id(current_user.user_id, with_party=True, with_role=True)


@users_router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: PasswordChange,
    current_user: UserAccount = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
):
    await controller.change_password(current_user.user_id, data)


@users_router.get(
    "",
    response_model=PaginatedResponse[UserAccountResponse],
    dependencies=[Depends(require_permission("user.read"))],
)
async def list_users(
    search: str | None = None,
    is_active: bool | None = None,
    pagination: PaginationParams = Depends(),
    controller: AuthController = Depends(get_auth_controller),
):
    items, total = await controller.list_users(
        pagination=pagination,
        search=search,
        is_active=is_active,
    )
    return paginate(items=items, total=total, pagination=pagination)


@users_router.get(
    "/{user_id}",
    response_model=UserAccountResponse,
    dependencies=[Depends(require_permission("user.read"))],
)
async def get_user(
    user_id: int,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.get_by_id(user_id, with_party=True, with_role=True)


@users_router.patch(
    "/{user_id}/status",
    response_model=UserAccountResponse,
    dependencies=[Depends(require_permission("user.update"))],
)
async def update_user_status(
    user_id: int,
    data: UserAccountUpdate,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.update_status(user_id, data)
