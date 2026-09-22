from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.auth.model import UserAccount
from app.modules.products.controller import ProductController
from app.modules.products.schemas import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.modules.rbac.dependencies import require_permission
from app.utils.pagination import PaginatedResponse, PaginationParams, paginate

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_controller(
    db: AsyncSession = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
) -> ProductController:
    return ProductController(db, current_user=current_user)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("product.create"))],
)
async def create_product(
    data: ProductCreate,
    controller: ProductController = Depends(get_product_controller),
):
    return await controller.create(data=data)


@router.get(
    "",
    response_model=PaginatedResponse[ProductResponse],
    dependencies=[Depends(require_permission("product.read"))],
)
async def list_products(
    search: str | None = None,
    is_active: bool | None = None,
    pagination: PaginationParams = Depends(),
    controller: ProductController = Depends(get_product_controller),
):
    items, total = await controller.list_products(
        pagination=pagination, search=search, is_active=is_active
    )
    return paginate(items, total, pagination)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_permission("product.read"))],
)
async def get_product(
    product_id: int,
    controller: ProductController = Depends(get_product_controller),
):
    return await controller.get_by_id(product_id)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_permission("product.update"))],
)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    controller: ProductController = Depends(get_product_controller),
):
    return await controller.update(product_id=product_id, data=data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("product.delete"))],
)
async def delete_product(
    product_id: int,
    controller: ProductController = Depends(get_product_controller),
):
    await controller.deactivate(product_id)
