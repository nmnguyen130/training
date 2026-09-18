from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# Permission Schemas
class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    permission_id: int
    permission_code: str
    description: str | None = None
    is_active: bool


# Role Schemas
class RoleBase(BaseModel):
    role_code: str = Field(min_length=2, max_length=50)
    role_name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class RoleCreate(RoleBase):
    permission_ids: list[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    role_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class RoleResponse(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    role_id: int
    is_system: bool
    is_active: bool


class RoleDetailResponse(RoleResponse):
    permissions: list[PermissionResponse] = Field(default_factory=list)


# Assignment Schemas
class RolePermissionsAssign(BaseModel):
    permission_ids: list[int]


class UserRoleAssign(BaseModel):
    role_id: int


class UserRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role_id: int
    assigned_at: datetime
    assigned_by: int | None = None
    role: RoleResponse
