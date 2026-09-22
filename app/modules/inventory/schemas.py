from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


# Inventory Schemas
class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inventory_id: int
    location_id: int
    product_id: int
    quantity_on_hand: Decimal
    reserved_quantity: Decimal
    available_quantity: Decimal
    last_counted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class InventoryDetailResponse(InventoryResponse):
    product_sku: str | None = None
    product_name: str | None = None
    location_code: str | None = None
    warehouse_id: int | None = None


# Operation Requests
class StockReceiptRequest(BaseModel):
    product_id: int
    to_location_id: int
    quantity: Decimal = Field(..., gt=0, decimal_places=4)
    reference_code: str | None = Field(None, max_length=100)
    note: str | None = Field(None, max_length=500)


class StockTransferRequest(BaseModel):
    product_id: int
    from_location_id: int
    to_location_id: int
    quantity: Decimal = Field(..., gt=0, decimal_places=4)
    reference_code: str | None = Field(None, max_length=100)
    note: str | None = Field(None, max_length=500)


class StockAdjustmentRequest(BaseModel):
    product_id: int
    location_id: int
    actual_quantity: Decimal = Field(..., ge=0, decimal_places=4)
    reference_code: str | None = Field(None, max_length=100)
    note: str | None = Field(None, max_length=500)


# Movement / Ledger Schemas
class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movement_id: int
    movement_type: str
    reference_code: str | None
    product_id: int
    from_location_id: int | None
    to_location_id: int | None
    quantity: Decimal
    note: str | None
    performed_by: int | None
    occurred_at: datetime
