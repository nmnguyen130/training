from datetime import datetime, timezone
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceError
from app.modules.auth.model import UserAccount
from app.modules.products.model import Product
from app.modules.products.schemas import ProductCreate, ProductUpdate
from app.utils.pagination import PaginationParams


class ProductController:
    def __init__(
        self,
        db: AsyncSession,
        current_user: UserAccount | None = None,
    ) -> None:
        self.db = db
        self.current_user = current_user

    async def get_by_id(self, product_id: int) -> Product:
        stmt = select(Product).where(Product.product_id == product_id)
        product = await self.db.scalar(stmt)
        if not product:
            raise ServiceError.not_found("Product")
        return product

    async def get_by_sku(self, sku: str) -> Product | None:
        stmt = select(Product).where(Product.sku == sku.strip())
        return await self.db.scalar(stmt)

    async def list_products(
        self,
        pagination: PaginationParams,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Product], int]:
        filters = []
        if is_active is not None:
            filters.append(Product.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Product.sku.ilike(pattern),
                    Product.name.ilike(pattern),
                    Product.barcode.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(Product).where(*filters)
        stmt = (
            select(Product)
            .where(*filters)
            .order_by(Product.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        products = list((await self.db.scalars(stmt)).all())

        if pagination.page == 1 and len(products) < pagination.limit:
            total = len(products)
        else:
            total = await self.db.scalar(count_stmt) or 0

        return products, total

    async def create(self, data: ProductCreate) -> Product:
        sku = data.sku.strip()
        sku_exists = await self.db.scalar(
            select(Product.product_id).where(Product.sku == sku)
        )
        if sku_exists:
            raise ServiceError.conflict(f"Product SKU '{sku}' is already taken")

        barcode = data.barcode.strip() if data.barcode else None
        if barcode:
            barcode_exists = await self.db.scalar(
                select(Product.product_id).where(Product.barcode == barcode)
            )
            if barcode_exists:
                raise ServiceError.conflict(f"Barcode '{barcode}' is already taken")

        product = Product(
            sku=sku,
            barcode=barcode,
            name=data.name.strip(),
            unit=data.unit.strip(),
            price=data.price,
            description=data.description,
            is_active=data.is_active,
        )
        self.db.add(product)
        await self.db.flush()
        await self.db.commit()
        return product

    async def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = await self.get_by_id(product_id)
        update_data = data.model_dump(exclude_unset=True)

        if "sku" in update_data:
            sku = update_data["sku"].strip()
            if sku != product.sku:
                sku_exists = await self.db.scalar(
                    select(Product.product_id).where(
                        Product.sku == sku,
                        Product.product_id != product_id,
                    )
                )
                if sku_exists:
                    raise ServiceError.conflict(f"Product SKU '{sku}' is already taken")
            update_data["sku"] = sku

        if "barcode" in update_data:
            barcode = update_data["barcode"].strip() if update_data["barcode"] else None
            if barcode and barcode != product.barcode:
                barcode_exists = await self.db.scalar(
                    select(Product.product_id).where(
                        Product.barcode == barcode,
                        Product.product_id != product_id,
                    )
                )
                if barcode_exists:
                    raise ServiceError.conflict(f"Barcode '{barcode}' is already taken")
            update_data["barcode"] = barcode

        for field, value in update_data.items():
            setattr(product, field, value)

        product.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return product

    async def deactivate(self, product_id: int) -> Product:
        product = await self.get_by_id(product_id)
        product.is_active = False
        product.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return product
