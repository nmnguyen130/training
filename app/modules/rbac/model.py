from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.auth.model import UserAccount


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary="role_permissions", viewonly=True
    )
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )


class Permission(Base):
    __tablename__ = "permissions"

    permission_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    permission_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("permissions.permission_id", ondelete="CASCADE"), primary_key=True
    )

    role: Mapped["Role"] = relationship("Role", back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship("Permission", back_populates="role_permissions")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_accounts.user_id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    assigned_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("user_accounts.user_id", ondelete="SET NULL"), nullable=True
    )

    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
    user: Mapped["UserAccount"] = relationship(
        "UserAccount", foreign_keys=[user_id], back_populates="user_roles"
    )
    assigner: Mapped["UserAccount | None"] = relationship("UserAccount", foreign_keys=[assigned_by])
