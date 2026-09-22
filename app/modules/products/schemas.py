from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    barcode: str | None = Field(None, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    unit: str = Field(default="item", max_length=30)
    price: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    description: str | None = None
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = Field(None, min_length=1, max_length=50)
    barcode: str | None = Field(None, max_length=100)
    name: str | None = Field(None, min_length=1, max_length=255)
    unit: str | None = Field(None, max_length=30)
    price: Decimal | None = Field(None, ge=0, decimal_places=2)
    description: str | None = None
    is_active: bool | None = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    created_at: datetime
    updated_at: datetime
