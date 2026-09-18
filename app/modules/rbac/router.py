from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.auth.model import UserAccount
from app.modules.rbac.controller import RbacController
from app.modules.rbac.dependencies import require_permission
from app.modules.rbac.schemas import (
    PermissionResponse,
    RoleCreate,
    RoleDetailResponse,
    RolePermissionsAssign,
    RoleResponse,
    RoleUpdate,
    UserRoleAssign,
    UserRoleResponse,
)
from app.utils.pagination import PaginatedResponse, PaginationParams, paginate

roles_router = APIRouter(prefix="/roles", tags=["Roles"])
permissions_router = APIRouter(prefix="/permissions", tags=["Permissions"])
user_roles_router = APIRouter(prefix="/users", tags=["User Roles"])


def get_rbac_controller(db: AsyncSession = Depends(get_db)) -> RbacController:
    return RbacController(db)


# Roles Endpoints
@roles_router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("role.create"))],
)
async def create_role(
    data: RoleCreate,
    controller: RbacController = Depends(get_rbac_controller),
):
    return await controller.create_role(data)


@roles_router.get(
    "",
    response_model=PaginatedResponse[RoleDetailResponse],
    dependencies=[Depends(require_permission("role.read"))],
)
async def list_roles(
    search: str | None = None,
    is_active: bool | None = None,
    pagination: PaginationParams = Depends(),
    controller: RbacController = Depends(get_rbac_controller),
):
    items, total = await controller.list_roles(
        pagination=pagination, search=search, is_active=is_active
    )
    return paginate(items=items, total=total, pagination=pagination)


@roles_router.get(
    "/{role_id}",
    response_model=RoleDetailResponse,
    dependencies=[Depends(require_permission("role.read"))],
)
async def get_role(
    role_id: int,
    controller: RbacController = Depends(get_rbac_controller),
):
    return await controller.get_role_by_id(role_id, with_permissions=True)


@roles_router.patch(
    "/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_permission("role.update"))],
)
async def update_role(
    role_id: int,
    data: RoleUpdate,
    controller: RbacController = Depends(get_rbac_controller),
):
    return await controller.update_role(role_id, data)


@roles_router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("role.delete"))],
)
async def delete_role(
    role_id: int,
    controller: RbacController = Depends(get_rbac_controller),
):
    await controller.delete_role(role_id)


@roles_router.put(
    "/{role_id}/permissions",
    response_model=RoleDetailResponse,
    dependencies=[Depends(require_permission("role.update"))],
)
async def set_role_permissions(
    role_id: int,
    data: RolePermissionsAssign,
    controller: RbacController = Depends(get_rbac_controller),
):
    return await controller.set_role_permissions(role_id, data.permission_ids)


# Permissions Endpoints (Read-only catalog for UI)
@permissions_router.get(
    "",
    response_model=PaginatedResponse[PermissionResponse],
    dependencies=[Depends(require_permission("permission.read"))],
)
async def list_permissions(
    search: str | None = None,
    is_active: bool | None = None,
    pagination: PaginationParams = Depends(),
    controller: RbacController = Depends(get_rbac_controller),
):
    items, total = await controller.list_permissions(
        pagination=pagination, search=search, is_active=is_active
    )
    return paginate(items=items, total=total, pagination=pagination)


# User Roles Endpoints
@user_roles_router.put(
    "/{user_id}/roles",
    response_model=list[UserRoleResponse],
    dependencies=[Depends(require_permission("user.update"))],
)
async def assign_user_roles(
    user_id: int,
    data: UserRoleAssign,
    current_user: UserAccount = Depends(get_current_user),
    controller: RbacController = Depends(get_rbac_controller),
):
    return await controller.assign_user_roles(
        user_id=user_id, role_ids=data.role_ids, assigned_by=current_user.user_id
    )


@user_roles_router.get(
    "/{user_id}/roles",
    response_model=list[UserRoleResponse],
    dependencies=[Depends(require_permission("user.read"))],
)
async def get_user_roles(
    user_id: int,
    controller: RbacController = Depends(get_rbac_controller),
):
    return await controller.get_user_roles(user_id)
