from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=6, max_length=72)
    is_active: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
