from uuid import UUID
from sqlalchemy import bindparam, func, select, text
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

    async def get_by_owners(self, owners: list[str]) -> list[dict]:
        cleaned_owners: list[str] = []
        for item in owners:
            for part in item.split(","):
                val = part.strip().lower()
                if val:
                    cleaned_owners.append(val)
        cleaned_owners = list(dict.fromkeys(cleaned_owners))

        if not cleaned_owners:
            return []

        sql = text("""
            SELECT 
                p.id,
                p.title,
                p.description,
                p.price,
                p.owner_id,
                p.created_at,
                u.name AS owner_name,
                u.email AS owner_email
            FROM products p
            INNER JOIN users u ON p.owner_id = u.id
            WHERE LOWER(u.name) IN :owners
            ORDER BY p.created_at DESC
        """).bindparams(bindparam("owners", expanding=True))

        result = await self.db.execute(
            sql,
            {"owners": cleaned_owners}
        )
        return [dict(row) for row in result.mappings().all()]

    async def _test_get_by_owners(self, owners: list[str]) -> list[dict]:
        cleaned_owners: list[str] = []
        for item in owners:
            for part in item.split(","):
                val = part.strip().lower()
                if val:
                    cleaned_owners.append(val)
        cleaned_owners = list(dict.fromkeys(cleaned_owners))

        if not cleaned_owners:
            return []

        sql = text("""
            SELECT 
                p.id,
                p.title,
                p.description,
                p.price,
                p.owner_id,
                p.created_at,
                u.name AS owner_name,
                u.email AS owner_email
            FROM products p
            INNER JOIN users u ON p.owner_id = u.id
            WHERE LOWER(u.name) = ANY(:owners)
            ORDER BY p.created_at DESC
        """)

        result = await self.db.execute(
            sql,
            {"owners": cleaned_owners}
        )
        return [dict(row) for row in result.mappings().all()]

