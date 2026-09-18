from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.parties.model import PartyType


# Party Schemas
class PartyBase(BaseModel):
    party_type: PartyType = Field(default=PartyType.PERSON)
    display_name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None)


class PartyCreate(PartyBase):
    pass


class PartyUpdate(BaseModel):
    party_type: PartyType | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = Field(default=None, max_length=255)
    address: str | None = None
    is_active: bool | None = None


class PartyResponse(PartyBase):
    model_config = ConfigDict(from_attributes=True)

    party_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Customer Schemas
class CustomerCreate(BaseModel):
    customer_code: str = Field(min_length=2, max_length=50)
    display_name: str = Field(min_length=1, max_length=255)
    party_type: PartyType = Field(default=PartyType.PERSON)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=255)
    address: str | None = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    customer_code: str
    created_at: datetime
    party: PartyResponse | None = None


# Supplier Schemas
class SupplierCreate(BaseModel):
    supplier_code: str = Field(min_length=2, max_length=50)
    display_name: str = Field(min_length=1, max_length=255)
    party_type: PartyType = Field(default=PartyType.ORGANIZATION)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=255)
    address: str | None = None


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    supplier_id: int
    supplier_code: str
    created_at: datetime
    party: PartyResponse | None = None


class PartyDetailResponse(PartyResponse):
    customer: CustomerResponse | None = None
    supplier: SupplierResponse | None = None
