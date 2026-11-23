
#Successfully parsed records
#It stores the structured financial transactions extracted by our Phase 1 parser.

"""Parsed mobile money transaction database model."""

from typing import TYPE_CHECKING
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.upload import Upload
    from app.models.user import User


class Transaction(Base):
    """A successfully parsed mobile money transaction."""

    __tablename__ = "transactions"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "transaction_id",
            name="uq_transaction_user_transaction_id",
        ),
        Index(
            "ix_transactions_user_timestamp",
            "user_id",
            "timestamp",
        ),
        Index(
            "ix_transactions_user_type",
            "user_id",
            "transaction_type",
        ),
        Index(
            "ix_transactions_user_provider",
            "user_id",
            "provider",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    upload_id: Mapped[int | None] = mapped_column(
        ForeignKey("uploads.id", ondelete="SET NULL"),
        nullable=True,
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    transaction_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    fee: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )
    balance_after: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    counterparty: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    raw_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="transactions",
    )
    upload: Mapped["Upload | None"] = relationship(
        back_populates="transactions",
    )
    category: Mapped["Category | None"] = relationship(
        back_populates="transactions",
    )
