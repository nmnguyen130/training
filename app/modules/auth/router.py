from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.auth.controller import AuthController
from app.modules.auth.model import User
from app.modules.auth.schemas import (
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
users_router = APIRouter(prefix="/users", tags=["Users"])


def get_auth_controller(db: AsyncSession = Depends(get_db)) -> AuthController:
    return AuthController(db)


# Auth Endpoints

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.register(data)


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

@users_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@users_router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.update(user=current_user, data=data)
