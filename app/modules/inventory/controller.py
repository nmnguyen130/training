from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceError
from app.modules.auth.model import UserAccount
from app.modules.inventory.model import Inventory, InventoryMovement
from app.modules.inventory.schemas import (
    StockAdjustmentRequest,
    StockReceiptRequest,
    StockTransferRequest,
)
from app.modules.products.model import Product
from app.modules.warehouse.model import Location
from app.utils.pagination import PaginationParams


class InventoryController:
    def __init__(
        self,
        db: AsyncSession,
        current_user: UserAccount | None = None,
    ) -> None:
        self.db = db
        self.current_user = current_user

    async def _validate_storage_location(self, location_id: int) -> Location:
        """Validate that the location exists, is active, and can store inventory."""
        stmt = select(Location).where(Location.location_id == location_id)
        location = await self.db.scalar(stmt)
        if not location:
            raise ServiceError.not_found("Location")
        if not location.is_active:
            raise ServiceError.bad_request(f"Location '{location.location_code}' is inactive")
        if not location.can_store_inventory:
            raise ServiceError.bad_request(
                f"Location '{location.location_code}' is a structural node and cannot store inventory directly"
            )
        return location

    async def _validate_product(self, product_id: int) -> Product:
        """Validate that the product exists and is active."""
        stmt = select(Product).where(Product.product_id == product_id)
        product = await self.db.scalar(stmt)
        if not product:
            raise ServiceError.not_found("Product")
        if not product.is_active:
            raise ServiceError.bad_request(f"Product '{product.sku}' is inactive")
        return product

    async def list_inventory(
        self,
        warehouse_id: int | None = None,
        location_id: int | None = None,
        product_id: int | None = None,
        pagination: PaginationParams = PaginationParams(),
    ) -> tuple[list[Inventory], int]:
        filters = []
        needs_location_join = False

        if warehouse_id is not None:
            filters.append(Location.warehouse_id == warehouse_id)
            needs_location_join = True
        if location_id is not None:
            filters.append(Inventory.location_id == location_id)
        if product_id is not None:
            filters.append(Inventory.product_id == product_id)

        count_stmt = select(func.count()).select_from(Inventory)
        stmt = select(Inventory)

        if needs_location_join:
            count_stmt = count_stmt.join(Location)
            stmt = stmt.join(Location)

        count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.where(*filters)
            .order_by(Inventory.inventory_id.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        items = list((await self.db.scalars(stmt)).all())

        if pagination.page == 1 and len(items) < pagination.limit:
            total = len(items)
        else:
            total = await self.db.scalar(count_stmt) or 0

        return items, total

    async def receive_stock(
        self,
        data: StockReceiptRequest,
        user_id: int | None = None,
    ) -> Inventory:
        """Receive inventory stock into a storage location."""
        effective_user_id = user_id or getattr(self.current_user, "user_id", None)
        await self._validate_product(data.product_id)
        await self._validate_storage_location(data.to_location_id)

        # 1. Acquire row lock or create inventory record
        stmt = (
            select(Inventory)
            .where(
                Inventory.location_id == data.to_location_id,
                Inventory.product_id == data.product_id,
            )
            .with_for_update()
        )
        inv = await self.db.scalar(stmt)

        if not inv:
            inv = Inventory(
                location_id=data.to_location_id,
                product_id=data.product_id,
                quantity_on_hand=data.quantity,
                reserved_quantity=Decimal("0.0000"),
            )
            self.db.add(inv)
        else:
            inv.quantity_on_hand += data.quantity
            inv.updated_at = datetime.now(timezone.utc)

        # 2. Record inventory movement in ledger
        movement = InventoryMovement(
            movement_type="RECEIPT",
            product_id=data.product_id,
            from_location_id=None,
            to_location_id=data.to_location_id,
            quantity=data.quantity,
            reference_code=data.reference_code,
            performed_by=effective_user_id,
            note=data.note,
        )
        self.db.add(movement)

        await self.db.flush()
        await self.db.commit()
        return inv

    async def transfer_stock(
        self,
        data: StockTransferRequest,
        user_id: int | None = None,
    ) -> tuple[Inventory, Inventory]:
        """Transfer stock between two valid storage locations."""
        effective_user_id = user_id or getattr(self.current_user, "user_id", None)
        if data.from_location_id == data.to_location_id:
            raise ServiceError.bad_request("Source and destination locations must be different")

        await self._validate_product(data.product_id)
        await self._validate_storage_location(data.from_location_id)
        await self._validate_storage_location(data.to_location_id)

        # 1. Lock and validate source inventory
        source_stmt = (
            select(Inventory)
            .where(
                Inventory.location_id == data.from_location_id,
                Inventory.product_id == data.product_id,
            )
            .with_for_update()
        )
        source_inv = await self.db.scalar(source_stmt)
        if not source_inv or source_inv.available_quantity < data.quantity:
            available = source_inv.available_quantity if source_inv else Decimal("0")
            raise ServiceError.bad_request(
                f"Insufficient available stock at source location. Available: {available}, Requested: {data.quantity}"
            )

        # 2. Lock or create destination inventory
        dest_stmt = (
            select(Inventory)
            .where(
                Inventory.location_id == data.to_location_id,
                Inventory.product_id == data.product_id,
            )
            .with_for_update()
        )
        dest_inv = await self.db.scalar(dest_stmt)
        if not dest_inv:
            dest_inv = Inventory(
                location_id=data.to_location_id,
                product_id=data.product_id,
                quantity_on_hand=data.quantity,
                reserved_quantity=Decimal("0.0000"),
            )
            self.db.add(dest_inv)
        else:
            dest_inv.quantity_on_hand += data.quantity
            dest_inv.updated_at = datetime.now(timezone.utc)

        # Deduct from source inventory
        source_inv.quantity_on_hand -= data.quantity
        source_inv.updated_at = datetime.now(timezone.utc)

        # 3. Record transfer movement
        movement = InventoryMovement(
            movement_type="TRANSFER",
            product_id=data.product_id,
            from_location_id=data.from_location_id,
            to_location_id=data.to_location_id,
            quantity=data.quantity,
            reference_code=data.reference_code,
            performed_by=effective_user_id,
            note=data.note,
        )
        self.db.add(movement)

        await self.db.flush()
        await self.db.commit()
        return source_inv, dest_inv

    async def adjust_stock(
        self,
        data: StockAdjustmentRequest,
        user_id: int | None = None,
    ) -> Inventory:
        """Adjust inventory stock based on physical count."""
        effective_user_id = user_id or getattr(self.current_user, "user_id", None)
        await self._validate_product(data.product_id)
        await self._validate_storage_location(data.location_id)

        stmt = (
            select(Inventory)
            .where(
                Inventory.location_id == data.location_id,
                Inventory.product_id == data.product_id,
            )
            .with_for_update()
        )
        inv = await self.db.scalar(stmt)

        current_qty = inv.quantity_on_hand if inv else Decimal("0.0000")
        diff = data.actual_quantity - current_qty

        if diff == 0:
            if inv:
                inv.last_counted_at = datetime.now(timezone.utc)
                inv.updated_at = datetime.now(timezone.utc)
                await self.db.commit()
                return inv
            return await self.receive_stock(
                StockReceiptRequest(
                    product_id=data.product_id,
                    to_location_id=data.location_id,
                    quantity=Decimal("0.0000"),
                    reference_code=data.reference_code,
                    note=data.note,
                ),
                user_id=effective_user_id,
            )

        if inv and data.actual_quantity < inv.reserved_quantity:
            raise ServiceError.bad_request(
                f"Cannot adjust stock below reserved quantity ({inv.reserved_quantity})"
            )

        now = datetime.now(timezone.utc)
        if not inv:
            inv = Inventory(
                location_id=data.location_id,
                product_id=data.product_id,
                quantity_on_hand=data.actual_quantity,
                reserved_quantity=Decimal("0.0000"),
                last_counted_at=now,
            )
            self.db.add(inv)
        else:
            inv.quantity_on_hand = data.actual_quantity
            inv.last_counted_at = now
            inv.updated_at = now

        # Record adjustment movement
        movement = InventoryMovement(
            movement_type="ADJUSTMENT",
            product_id=data.product_id,
            from_location_id=data.location_id if diff < 0 else None,
            to_location_id=data.location_id if diff > 0 else None,
            quantity=abs(diff),
            reference_code=data.reference_code,
            performed_by=effective_user_id,
            note=data.note or f"Stock adjustment diff: {diff:+.4f}",
        )
        self.db.add(movement)

        await self.db.flush()
        await self.db.commit()
        return inv

    async def list_movements(
        self,
        product_id: int | None = None,
        location_id: int | None = None,
        movement_type: str | None = None,
        reference_code: str | None = None,
        pagination: PaginationParams = PaginationParams(),
    ) -> tuple[list[InventoryMovement], int]:
        filters = []
        if product_id is not None:
            filters.append(InventoryMovement.product_id == product_id)
        if location_id is not None:
            filters.append(
                or_(
                    InventoryMovement.from_location_id == location_id,
                    InventoryMovement.to_location_id == location_id,
                )
            )
        if movement_type:
            filters.append(InventoryMovement.movement_type == movement_type.strip().upper())
        if reference_code:
            filters.append(
                InventoryMovement.reference_code.ilike(f"%{reference_code.strip()}%")
            )

        count_stmt = select(func.count()).select_from(InventoryMovement).where(*filters)
        stmt = (
            select(InventoryMovement)
            .where(*filters)
            .order_by(InventoryMovement.occurred_at.desc(), InventoryMovement.movement_id.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        items = list((await self.db.scalars(stmt)).all())

        if pagination.page == 1 and len(items) < pagination.limit:
            total = len(items)
        else:
            total = await self.db.scalar(count_stmt) or 0

        return items, total
