from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.parties.model import Party


class UserAccount(Base):
    __tablename__ = "user_accounts"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    party_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("parties.party_id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
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

    # Unidirectional relationship: UserAccount -> Party
    party: Mapped[Party] = relationship(Party)
