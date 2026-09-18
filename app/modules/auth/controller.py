from datetime import datetime, timezone
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ServiceError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth.model import UserAccount
from app.modules.auth.schemas import (
    PasswordChange,
    TokenResponse,
    UserAccountUpdate,
    UserCreate,
    UserLogin,
)
from app.modules.parties.model import Party, PartyType
from app.modules.rbac.model import Role, UserRole
from app.utils.pagination import PaginationParams


class AuthController:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(
        self, user_id: int, with_party: bool = False, with_role: bool = False
    ) -> UserAccount:
        stmt = select(UserAccount).where(UserAccount.user_id == user_id)
        if with_party:
            stmt = stmt.options(selectinload(UserAccount.party))
        user = await self.db.scalar(stmt)
        if not user:
            raise ServiceError.not_found("User")
        if with_role:
            user_role = await self.db.scalar(
                select(UserRole).options(selectinload(UserRole.role)).where(UserRole.user_id == user_id)
            )
            if user_role:
                user.role = user_role.role
        return user

    async def get_by_username(self, username: str) -> UserAccount | None:
        return await self.db.scalar(
            select(UserAccount).where(UserAccount.username == username)
        )

    def create_tokens(self, user: UserAccount) -> TokenResponse:
        access_token = create_access_token(user_id=user.user_id)
        refresh_token, _, _ = create_refresh_token(user_id=user.user_id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def create_user(
        self, data: UserCreate, assigned_by: int | None = None
    ) -> UserAccount:
        # 1. Validate role and username
        role = await self.db.get(Role, data.role_id)
        if not role or not role.is_active:
            raise ServiceError.bad_request(f"Role #{data.role_id} not found or inactive")

        existing_user = await self.get_by_username(data.username)
        if existing_user:
            raise ServiceError.conflict(f"Username '{data.username}' is already taken")

        # 2. Create party and user account
        party = Party(
            party_type=PartyType.PERSON,
            display_name=data.display_name,
            email=data.email,
            phone=data.phone,
        )
        user = UserAccount(
            party=party,
            username=data.username,
            password_hash=hash_password(data.password),
        )
        user_role = UserRole(user=user, role_id=role.role_id, assigned_by=assigned_by)
        self.db.add_all([party, user, user_role])

        # 3. Commit
        await self.db.commit()

        user.party, user.role = party, role
        return user

    async def login(self, data: UserLogin) -> TokenResponse:
        user = await self.get_by_username(data.username)
        if not user or not verify_password(data.password, user.password_hash):
            raise ServiceError.unauthorized("Incorrect username or password")
        if not user.is_active:
            raise ServiceError.bad_request("User account is inactive")

        return self.create_tokens(user)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
            user_id = int(payload["sub"])
        except Exception:
            raise ServiceError.unauthorized("Invalid or expired refresh token")

        user = await self.get_by_id(user_id)
        if not user.is_active:
            raise ServiceError.unauthorized("User account is inactive")

        return self.create_tokens(user)

    async def change_password(self, user_id: int, data: PasswordChange) -> None:
        user = await self.get_by_id(user_id)
        if not verify_password(data.old_password, user.password_hash):
            raise ServiceError.bad_request("Current password does not match")

        user.password_hash = hash_password(data.new_password)
        await self.db.commit()

    async def update_status(self, user_id: int, data: UserAccountUpdate) -> UserAccount:
        user = await self.get_by_id(user_id, with_party=True)
        user.is_active = data.is_active
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return user

    async def list_users(
        self,
        pagination: PaginationParams,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[UserAccount], int]:
        filters = []

        if is_active is not None:
            filters.append(UserAccount.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    UserAccount.username.ilike(pattern),
                    UserAccount.party.has(Party.display_name.ilike(pattern)),
                    UserAccount.party.has(Party.email.ilike(pattern)),
                )
            )

        count_stmt = select(func.count()).select_from(UserAccount).where(*filters)
        stmt = (
            select(UserAccount)
            .options(selectinload(UserAccount.party))
            .where(*filters)
            .order_by(UserAccount.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )

        users = list((await self.db.scalars(stmt)).all())

        if pagination.page == 1 and len(users) < pagination.limit:
            total = len(users)
        else:
            total = await self.db.scalar(count_stmt) or 0

        return users, total
