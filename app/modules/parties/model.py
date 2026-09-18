import enum
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PartyType(str, enum.Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"


class Party(Base):
    __tablename__ = "parties"

    party_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    party_type: Mapped[PartyType] = mapped_column(
        String(20),
        default=PartyType.PERSON,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    customer: Mapped["Customer | None"] = relationship(
        "Customer",
        back_populates="party",
        uselist=False,
    )
    supplier: Mapped["Supplier | None"] = relationship(
        "Supplier",
        back_populates="party",
        uselist=False,
    )


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("parties.party_id", ondelete="CASCADE"),
        primary_key=True,
    )
    customer_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    party: Mapped["Party"] = relationship("Party", back_populates="customer")


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("parties.party_id", ondelete="CASCADE"),
        primary_key=True,
    )
    supplier_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    party: Mapped["Party"] = relationship("Party", back_populates="supplier")
