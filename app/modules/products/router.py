from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.core.pagination import PaginatedResponse, PaginationParams, paginate
from app.modules.auth.model import User
from app.modules.products.controller import ProductController
from app.modules.products.schemas import (
    ProductCreate,
    ProductResponse,
    ProductWithOwnerResponse,
)

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_controller(db: AsyncSession = Depends(get_db)) -> ProductController:
    return ProductController(db)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    current_user: User = Depends(get_current_user),
    controller: ProductController = Depends(get_product_controller),
):
    return await controller.create(owner_id=current_user.id, data=data)


@router.get("", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    pagination: PaginationParams = Depends(),
    controller: ProductController = Depends(get_product_controller),
):
    items, total = await controller.list_all(pagination)
    return paginate(items, total, pagination)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    controller: ProductController = Depends(get_product_controller),
):
    return await controller.get_by_id(product_id)


@router.get("/by-owners", response_model=list[ProductWithOwnerResponse])
async def get_products_by_owners(
    owners: list[str] = Query(...),
    controller: ProductController = Depends(get_product_controller),
):
    return await controller.get_by_owners(owners)
