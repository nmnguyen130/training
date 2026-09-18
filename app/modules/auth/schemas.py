from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.parties.schemas import PartyResponse


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=72)
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    party_id: int | None = None


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"


class PasswordChange(BaseModel):
    old_password: str = Field(min_length=6, max_length=72)
    new_password: str = Field(min_length=6, max_length=72)


class UserAccountUpdate(BaseModel):
    is_active: bool | None = None


class UserAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    party_id: int
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    party: PartyResponse | None = None
