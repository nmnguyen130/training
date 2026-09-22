from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


# Warehouse Schemas
class WarehouseBase(BaseModel):
    warehouse_id: int | None = None
    warehouse_code: str | None = Field(None, min_length=1, max_length=50)
    warehouse_name: str | None = Field(None, min_length=1, max_length=100)
    address: str | None = None
    description: str | None = None
    is_active: bool | None = True


class WarehouseCreate(WarehouseBase):
    pass


# class WarehouseUpdate(BaseModel):
#     warehouse_id: int
#     warehouse_code: str | None = Field(None, min_length=1, max_length=50)
#     warehouse_name: str | None = Field(None, min_length=1, max_length=100)
#     address: str | None = None
#     description: str | None = None
#     is_active: bool | None = None


class WarehouseResponse(WarehouseBase):
    model_config = ConfigDict(from_attributes=True)

    warehouse_id: int
    created_at: datetime
    updated_at: datetime


# Location Schemas
class LocationBase(BaseModel):
    warehouse_id: int
    parent_location_id: int | None = None
    location_code: str = Field(min_length=1, max_length=50)
    location_name: str = Field(min_length=1, max_length=100)
    barcode: str | None = Field(None, max_length=100)
    location_type: str
    location_purpose: str = Field(default="STORAGE")
    can_store_inventory: bool = Field(default=False)
    max_weight_kg: Decimal | None = Field(default=None, ge=0)
    sort_order: int = Field(default=0)
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    parent_location_id: int | None = None
    location_code: str | None = Field(None, min_length=1, max_length=50)
    location_name: str | None = Field(None, min_length=1, max_length=100)
    barcode: str | None = None
    location_type: str | None = None
    location_purpose: str | None = None
    can_store_inventory: bool | None = None
    max_weight_kg: Decimal | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class LocationResponse(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    location_id: int
    created_at: datetime
    updated_at: datetime


class LocationTreeResponse(LocationResponse):
    children: list["LocationTreeResponse"] = Field(default_factory=list)
