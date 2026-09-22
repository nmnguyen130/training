from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.auth.model import UserAccount
from app.modules.rbac.dependencies import require_permission
from app.modules.warehouse.controller import LocationController, WarehouseController
from app.modules.warehouse.schemas import (
    LocationCreate,
    LocationResponse,
    LocationTreeResponse,
    LocationUpdate,
    WarehouseCreate,
    WarehouseResponse,
    # WarehouseUpdate,
    WarehouseBase
)
from app.utils.pagination import PaginatedResponse, PaginationParams, paginate

router = APIRouter(tags=["Warehouse & Locations"])


def get_warehouse_controller(
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
) -> WarehouseController:
    return WarehouseController(db, current_user=current_user)


def get_location_controller(
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
) -> LocationController:
    return LocationController(db, current_user=current_user)


# WAREHOUSES
@router.post(
    "/warehouses",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("warehouse.create"))],
)
async def create_warehouse(
    data: WarehouseCreate,
    controller: WarehouseController = Depends(get_warehouse_controller),
):
    return await controller.create(data)


@router.get(
    "/warehouses",
    response_model=PaginatedResponse[WarehouseResponse],
    dependencies=[Depends(require_permission("warehouse.read"))],
)
async def list_warehouses(
    search: str | None = None,
    is_active: bool | None = None,
    pagination: PaginationParams = Depends(),
    controller: WarehouseController = Depends(get_warehouse_controller),
):
    items, total = await controller.list_warehouses(
        pagination=pagination, search=search, is_active=is_active
    )
    return paginate(items, total, pagination)


@router.get(
    "/warehouses/{warehouse_id}",
    response_model=WarehouseResponse,
    dependencies=[Depends(require_permission("warehouse.read"))],
)
async def get_warehouse(
    warehouse_id: int,
    controller: WarehouseController = Depends(get_warehouse_controller),
):
    return await controller.get_by_id(warehouse_id)


@router.patch(
    "/warehouses/",
    response_model=WarehouseResponse,
    dependencies=[Depends(require_permission("warehouse.update"))],
)
async def update_warehouse(
    # warehouse_id: int,
    data: WarehouseBase,
    controller: WarehouseController = Depends(get_warehouse_controller),
):
    return await controller.update(data)


@router.delete(
    "/warehouses/{warehouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("warehouse.delete"))],
)
async def delete_warehouse(
    warehouse_id: int,
    controller: WarehouseController = Depends(get_warehouse_controller),
):
    await controller.deactivate(warehouse_id)


# LOCATIONS
@router.post(
    "/locations",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("warehouse.create"))],
)
async def create_location(
    data: LocationCreate,
    controller: LocationController = Depends(get_location_controller),
):
    return await controller.create(data)


@router.get(
    "/locations/{location_id}",
    response_model=LocationResponse,
    dependencies=[Depends(require_permission("warehouse.read"))],
)
async def get_location(
    location_id: int,
    controller: LocationController = Depends(get_location_controller),
):
    return await controller.get_by_id(location_id)


@router.patch(
    "/locations/{location_id}",
    response_model=LocationResponse,
    dependencies=[Depends(require_permission("warehouse.update"))],
)
async def update_location(
    location_id: int,
    data: LocationUpdate,
    controller: LocationController = Depends(get_location_controller),
):
    return await controller.update(location_id, data)


@router.delete(
    "/locations/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("warehouse.delete"))],
)
async def delete_location(
    location_id: int,
    controller: LocationController = Depends(get_location_controller),
):
    await controller.deactivate(location_id)


@router.get(
    "/warehouses/{warehouse_id}/locations",
    response_model=list[LocationResponse],
    dependencies=[Depends(require_permission("warehouse.read"))],
)
async def list_warehouse_locations(
    warehouse_id: int,
    parent_location_id: int | None = None,
    can_store_inventory: bool | None = None,
    is_active: bool | None = None,
    controller: LocationController = Depends(get_location_controller),
):
    return await controller.list_by_warehouse(
        warehouse_id=warehouse_id,
        parent_location_id=parent_location_id,
        can_store_inventory=can_store_inventory,
        is_active=is_active,
    )


@router.get(
    "/warehouses/{warehouse_id}/locations/tree",
    response_model=list[LocationTreeResponse],
    dependencies=[Depends(require_permission("warehouse.read"))],
)
async def get_warehouse_location_tree(
    warehouse_id: int,
    controller: LocationController = Depends(get_location_controller),
):
    return await controller.get_tree(warehouse_id=warehouse_id)
