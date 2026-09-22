from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.auth.model import UserAccount
from app.modules.parties.controller import PartyController
from app.modules.parties.model import PartyType
from app.modules.parties.schemas import (
    CustomerCreate,
    CustomerResponse,
    PartyCreate,
    PartyDetailResponse,
    PartyResponse,
    PartyUpdate,
    SupplierCreate,
    SupplierResponse,
)
from app.modules.rbac.dependencies import require_permission
from app.utils.pagination import PaginatedResponse, PaginationParams, paginate

parties_router = APIRouter(prefix="/parties", tags=["Parties"])
customers_router = APIRouter(prefix="/customers", tags=["Customers"])
suppliers_router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


def get_party_controller(
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
) -> PartyController:
    return PartyController(db, current_user=current_user)


# Parties Endpoints
@parties_router.post(
    "",
    response_model=PartyResponse,
    status_code=status.HTTP_201_CREATED,
    # dependencies=[Depends(require_permission("party.create"))],
)
async def create_party(
    data: PartyCreate,
    controller: PartyController = Depends(get_party_controller),
):
    return await controller.create(data)


@parties_router.get(
    "",
    response_model=PaginatedResponse[PartyDetailResponse],
    dependencies=[Depends(require_permission("party.read"))],
)
async def list_parties(
    search: str | None = None,
    party_type: PartyType | None = None,
    is_active: bool | None = None,
    pagination: PaginationParams = Depends(),
    controller: PartyController = Depends(get_party_controller),
):
    items, total = await controller.list_parties(
        pagination=pagination,
        search=search,
        party_type=party_type,
        is_active=is_active,
    )
    return paginate(items=items, total=total, pagination=pagination)


@parties_router.get(
    "/{party_id}",
    response_model=PartyDetailResponse,
    dependencies=[Depends(require_permission("party.read"))],
)
async def get_party(
    party_id: int,
    controller: PartyController = Depends(get_party_controller),
):
    return await controller.get_by_id(party_id, with_relations=True)


@parties_router.patch(
    "/{party_id}",
    response_model=PartyResponse,
    dependencies=[Depends(require_permission("party.update"))],
)
async def update_party(
    party_id: int,
    data: PartyUpdate,
    controller: PartyController = Depends(get_party_controller),
):
    return await controller.update(party_id, data)


@parties_router.delete(
    "/{party_id}",
    response_model=PartyResponse,
    dependencies=[Depends(require_permission("party.delete"))],
)
async def deactivate_party(
    party_id: int,
    controller: PartyController = Depends(get_party_controller),
):
    return await controller.deactivate(party_id)


# Customers Endpoints
@customers_router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("customer.create"))],
)
async def create_customer(
    data: CustomerCreate,
    controller: PartyController = Depends(get_party_controller),
):
    return await controller.create_customer(data)


@customers_router.get(
    "",
    response_model=PaginatedResponse[CustomerResponse],
    dependencies=[Depends(require_permission("customer.read"))],
)
async def list_customers(
    pagination: PaginationParams = Depends(),
    controller: PartyController = Depends(get_party_controller),
):
    items, total = await controller.list_customers(pagination)
    return paginate(items=items, total=total, pagination=pagination)


@customers_router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    dependencies=[Depends(require_permission("customer.read"))],
)
async def get_customer(
    customer_id: int,
    controller: PartyController = Depends(get_party_controller),
):
    return await controller.get_customer(customer_id)


# Suppliers Endpoints
@suppliers_router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("supplier.create"))],
)
async def create_supplier(
    data: SupplierCreate,
    controller: PartyController = Depends(get_party_controller),
):
    return await controller.create_supplier(data)


@suppliers_router.get(
    "",
    response_model=PaginatedResponse[SupplierResponse],
    dependencies=[Depends(require_permission("supplier.read"))],
)
async def list_suppliers(
    pagination: PaginationParams = Depends(),
    controller: PartyController = Depends(get_party_controller),
):
    items, total = await controller.list_suppliers(pagination)
    return paginate(items=items, total=total, pagination=pagination)


@suppliers_router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    dependencies=[Depends(require_permission("supplier.read"))],
)
async def get_supplier(
    supplier_id: int,
    controller: PartyController = Depends(get_party_controller),
):
    return await controller.get_supplier(supplier_id)
