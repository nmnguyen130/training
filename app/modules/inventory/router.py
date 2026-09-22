from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.auth.model import UserAccount
from app.modules.inventory.controller import InventoryController
from app.modules.inventory.schemas import (
    InventoryMovementResponse,
    InventoryResponse,
    StockAdjustmentRequest,
    StockReceiptRequest,
    StockTransferRequest,
)
from app.modules.rbac.dependencies import require_permission
from app.utils.pagination import PaginatedResponse, PaginationParams, paginate

router = APIRouter(prefix="/inventory", tags=["Inventory & Movements"])


def get_inventory_controller(
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
) -> InventoryController:
    return InventoryController(db, current_user=current_user)


@router.get(
    "",
    response_model=PaginatedResponse[InventoryResponse],
    dependencies=[Depends(require_permission("inventory.read"))],
)
async def list_inventory(
    warehouse_id: int | None = None,
    location_id: int | None = None,
    product_id: int | None = None,
    pagination: PaginationParams = Depends(),
    controller: InventoryController = Depends(get_inventory_controller),
):
    items, total = await controller.list_inventory(
        warehouse_id=warehouse_id,
        location_id=location_id,
        product_id=product_id,
        pagination=pagination,
    )
    return paginate(items, total, pagination)


@router.post(
    "/receive",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("inventory.create"))],
)
async def receive_stock(
    data: StockReceiptRequest,
    current_user: UserAccount = Depends(get_current_user),
    controller: InventoryController = Depends(get_inventory_controller),
):
    """Receive goods into a storage location."""
    return await controller.receive_stock(data=data, user_id=current_user.user_id)


@router.post(
    "/transfer",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("inventory.update"))],
)
async def transfer_stock(
    data: StockTransferRequest,
    current_user: UserAccount = Depends(get_current_user),
    controller: InventoryController = Depends(get_inventory_controller),
):
    """Transfer goods between two storage locations atomically."""
    src, dst = await controller.transfer_stock(data=data, user_id=current_user.user_id)
    return {
        "message": "Stock transferred successfully",
        "source": InventoryResponse.model_validate(src),
        "destination": InventoryResponse.model_validate(dst),
    }


@router.post(
    "/adjust",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("inventory.update"))],
)
async def adjust_stock(
    data: StockAdjustmentRequest,
    current_user: UserAccount = Depends(get_current_user),
    controller: InventoryController = Depends(get_inventory_controller),
):
    """Adjust physical stock quantity after cycle count."""
    return await controller.adjust_stock(data=data, user_id=current_user.user_id)


@router.get(
    "/movements",
    response_model=PaginatedResponse[InventoryMovementResponse],
    dependencies=[Depends(require_permission("inventory.read"))],
)
async def list_movements(
    product_id: int | None = None,
    location_id: int | None = None,
    movement_type: str | None = None,
    reference_code: str | None = None,
    pagination: PaginationParams = Depends(),
    controller: InventoryController = Depends(get_inventory_controller),
):
    """Retrieve stock ledger movement history."""
    items, total = await controller.list_movements(
        product_id=product_id,
        location_id=location_id,
        movement_type=movement_type,
        reference_code=reference_code,
        pagination=pagination,
    )
    return paginate(items, total, pagination)
