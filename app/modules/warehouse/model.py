from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Warehouse(Base):
    __tablename__ = "warehouses"

    warehouse_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    warehouse_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    warehouse_name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    locations: Mapped[list["Location"]] = relationship(
        "Location", back_populates="warehouse", cascade="all, delete-orphan"
    )


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "location_code", name="uq_location_warehouse_code"),
        CheckConstraint(
            "parent_location_id IS NULL OR parent_location_id != location_id",
            name="chk_location_parent_not_self",
        ),
    )

    location_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("warehouses.warehouse_id", ondelete="CASCADE"), nullable=False
    )
    parent_location_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("locations.location_id", ondelete="RESTRICT"), nullable=True, index=True
    )

    location_code: Mapped[str] = mapped_column(String(50), nullable=False)
    location_name: Mapped[str] = mapped_column(String(100), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)

    location_type: Mapped[str] = mapped_column(String(30), nullable=False)
    location_purpose: Mapped[str] = mapped_column(String(30), default="STORAGE", nullable=False)
    can_store_inventory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    max_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="locations")
    parent: Mapped["Location | None"] = relationship(
        "Location", remote_side=[location_id], back_populates="children"
    )
    children: Mapped[list["Location"]] = relationship(
        "Location", back_populates="parent", cascade="all"
    )
