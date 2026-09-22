from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.auth.model import UserAccount
from app.modules.products.model import Product
from app.modules.warehouse.model import Location


class Inventory(Base):
    __tablename__ = "inventories"
    __table_args__ = (
        UniqueConstraint("location_id", "product_id", name="uq_inventory_location_product"),
        CheckConstraint("quantity_on_hand >= 0", name="chk_inventory_qoh_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="chk_inventory_reserved_non_negative"),
        CheckConstraint("reserved_quantity <= quantity_on_hand", name="chk_inventory_reserved_lte_qoh"),
    )

    inventory_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    location_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("locations.location_id", ondelete="RESTRICT"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False, index=True
    )

    quantity_on_hand: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0.0000"), nullable=False
    )
    reserved_quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0.0000"), nullable=False
    )

    last_counted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    location: Mapped["Location"] = relationship("Location")
    product: Mapped["Product"] = relationship("Product")

    @property
    def available_quantity(self) -> Decimal:
        return self.quantity_on_hand - self.reserved_quantity


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_movement_quantity_positive"),
        CheckConstraint(
            "from_location_id IS NOT NULL OR to_location_id IS NOT NULL",
            name="chk_movement_location_present",
        ),
    )

    movement_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    from_location_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("locations.location_id", ondelete="RESTRICT"), nullable=True, index=True
    )
    to_location_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("locations.location_id", ondelete="RESTRICT"), nullable=True, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    performed_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("user_accounts.user_id", ondelete="SET NULL"), nullable=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product")
    from_location: Mapped["Location | None"] = relationship(
        "Location", foreign_keys=[from_location_id]
    )
    to_location: Mapped["Location | None"] = relationship(
        "Location", foreign_keys=[to_location_id]
    )
    user: Mapped["UserAccount | None"] = relationship("UserAccount", foreign_keys=[performed_by])
