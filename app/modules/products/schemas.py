from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(gt=0, decimal_places=2)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    price: Decimal
    owner_id: UUID
    created_at: datetime


class ProductWithOwnerResponse(ProductResponse):
    owner_name: str
    owner_email: str
