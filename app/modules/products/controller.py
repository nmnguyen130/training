from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceError
from app.core.pagination import PaginationParams
from app.modules.products.model import Product
from app.modules.products.schemas import ProductCreate


class ProductController:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, product_id: UUID) -> Product:
        product = await self.db.get(Product, product_id)
        if not product:
            raise ServiceError.not_found("Product")
        return product

    async def list_all(self, pagination: PaginationParams) -> tuple[list[Product], int]:
        count_stmt = select(func.count()).select_from(Product)
        stmt = (
            select(Product)
            .order_by(Product.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        items = list((await self.db.scalars(stmt)).all())

        if pagination.page == 1 and len(items) < pagination.limit:
            total = len(items)
        else:
            total = await self.db.scalar(count_stmt) or 0

        return items, total

    async def create(self, owner_id: UUID, data: ProductCreate) -> Product:
        product = Product(
            title=data.title.strip(),
            description=data.description,
            price=data.price,
            owner_id=owner_id,
        )
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product
