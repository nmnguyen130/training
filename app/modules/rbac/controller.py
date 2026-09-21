from sqlalchemy import delete, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ServiceError
from app.modules.auth.model import UserAccount
from app.modules.rbac.constants import Role as RoleEnum
from app.modules.rbac.model import Permission, Role, RolePermission, UserRole
from app.modules.rbac.schemas import RoleCreate, RoleUpdate
from app.utils.pagination import PaginationParams


class RbacController:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # Permissions
    async def list_permissions(
        self,
        pagination: PaginationParams,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Permission], int]:
        filters = []
        if is_active is not None:
            filters.append(Permission.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Permission.permission_code.ilike(pattern),
                    Permission.description.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(Permission).where(*filters)
        stmt = (
            select(Permission)
            .where(*filters)
            .order_by(Permission.permission_code.asc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        items = list((await self.db.scalars(stmt)).all())

        if pagination.page == 1 and len(items) < pagination.limit:
            total = len(items)
        else:
            total = await self.db.scalar(count_stmt) or 0

        return items, total

    # Roles
    async def get_role_by_id(self, role_id: int, with_permissions: bool = False) -> Role:
        stmt = select(Role).where(Role.role_id == role_id)
        if with_permissions:
            stmt = stmt.options(selectinload(Role.permissions))

        role = await self.db.scalar(stmt)
        if not role:
            raise ServiceError.not_found("Role")
        return role

    async def create_role(self, data: RoleCreate) -> Role:
        exists = await self.db.scalar(select(Role.role_id).where(Role.role_code == data.role_code))
        if exists:
            raise ServiceError.conflict(f"Role code '{data.role_code}' already exists")

        role = Role(
            role_code=data.role_code,
            role_name=data.role_name,
            description=data.description,
            is_system=False,
            is_active=True,
        )
        self.db.add(role)
        await self.db.flush()

        if data.permission_ids:
            for pid in set(data.permission_ids):
                self.db.add(RolePermission(role_id=role.role_id, permission_id=pid))
            await self.db.flush()

        await self.db.commit()
        return role

    async def list_roles(
        self,
        pagination: PaginationParams,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Role], int]:
        filters = []
        if is_active is not None:
            filters.append(Role.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Role.role_code.ilike(pattern),
                    Role.role_name.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(Role).where(*filters)
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(*filters)
            .order_by(Role.role_code.asc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        items = list((await self.db.scalars(stmt)).all())

        if pagination.page == 1 and len(items) < pagination.limit:
            total = len(items)
        else:
            total = await self.db.scalar(count_stmt) or 0

        return items, total

    async def update_role(self, role_id: int, data: RoleUpdate) -> Role:
        role = await self.get_role_by_id(role_id)
        if role.is_system and data.is_active is False:
            raise ServiceError.forbidden("Cannot deactivate a system role")

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(role, field, value)

        await self.db.commit()
        return role

    async def delete_role(self, role_id: int) -> None:
        role = await self.get_role_by_id(role_id)
        if role.is_system:
            raise ServiceError.forbidden("Cannot delete a system role")
        await self.db.delete(role)
        await self.db.commit()

    async def set_role_permissions(self, role_id: int, permission_ids: list[int]) -> Role:
        role = await self.get_role_by_id(role_id)
        if role.is_system:
            raise ServiceError.forbidden("Cannot modify permissions of a system role directly")

        await self.db.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )
        for pid in set(permission_ids):
            self.db.add(RolePermission(role_id=role_id, permission_id=pid))

        await self.db.commit()
        return await self.get_role_by_id(role_id, with_permissions=True)

    # User Roles
    async def assign_user_role(
        self, user_id: int, role_id: int, assigned_by: int | None = None
    ) -> UserRole:
        user = await self.db.get(UserAccount, user_id)
        if not user:
            raise ServiceError.not_found("User")

        role = await self.get_role_by_id(role_id)
        if not role.is_active:
            raise ServiceError.bad_request("Role is inactive")

        await self.db.execute(delete(UserRole).where(UserRole.user_id == user_id))
        user_role = UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
        self.db.add(user_role)
        await self.db.commit()

        user_role.role = role
        return user_role

    async def get_user_role(self, user_id: int) -> UserRole | None:
        stmt = (
            select(UserRole)
            .where(UserRole.user_id == user_id)
            .options(selectinload(UserRole.role))
        )
        return await self.db.scalar(stmt)

    # Permission Checking Engine
    async def has_permission(self, user_id: int, permission_code: str) -> bool:
        user_role = await self.get_user_role(user_id)
        if not user_role or not user_role.role or not user_role.role.is_active:
            return False

        if user_role.role.role_code == RoleEnum.SUPER_ADMIN:
            return True

        stmt = select(
            select(1)
            .select_from(RolePermission)
            .join(Permission, RolePermission.permission_id == Permission.permission_id)
            .where(
                RolePermission.role_id == user_role.role_id,
                Permission.is_active.is_(True),
                Permission.permission_code == permission_code,
            )
            .exists()
        )
        return bool(await self.db.scalar(stmt))
