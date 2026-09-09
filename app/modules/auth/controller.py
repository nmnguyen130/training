from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth.model import User
from app.modules.auth.schemas import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserUpdate,
)


class AuthController:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.strip().lower())
        return await self.db.scalar(stmt)

    def create_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(user_id=user.id)
        refresh_token, _, _ = create_refresh_token(user_id=user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def register(self, data: UserCreate) -> User:
        email = data.email.strip().lower()
        existing_user = await self.get_by_email(email)
        if existing_user:
            raise ServiceError.conflict("Email already registered")

        user = User(
            name=data.name.strip(),
            email=email,
            hashed_password=hash_password(data.password),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def login(self, data: UserLogin) -> TokenResponse:
        user = await self.get_by_email(data.email)

        if not user or not verify_password(data.password, user.hashed_password):
            raise ServiceError.unauthorized("Incorrect email or password")
        if not user.is_active:
            raise ServiceError.bad_request("User account is inactive")

        return self.create_tokens(user)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
            user_id = UUID(payload["sub"])
        except Exception:
            raise ServiceError.unauthorized("Invalid or expired refresh token")

        user = await self.db.get(User, user_id)
        if not user or not user.is_active:
            raise ServiceError.unauthorized("Invalid or expired refresh token")

        return self.create_tokens(user)

    async def update(self, user: User, data: UserUpdate) -> User:
        if data.name is not None:
            user.name = data.name.strip()
        if data.password is not None:
            user.hashed_password = hash_password(data.password)
        if data.is_active is not None:
            user.is_active = data.is_active

        await self.db.flush()
        await self.db.refresh(user)
        return user
