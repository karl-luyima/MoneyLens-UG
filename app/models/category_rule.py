#User-defined matching rules

"""User-defined transaction categorization rules."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.category import Category
from app.models.user import User


class CategoryRule(Base):
    """A keyword rule that assigns transactions to a category."""

    __tablename__ = "category_rules"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "keyword",
            name="uq_category_rule_user_keyword",
        ),
        Index("ix_category_rules_user_active", "user_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    keyword: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    match_field: Mapped[str] = mapped_column(
        String(50),
        default="counterparty",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="category_rules",
    )
    category: Mapped["Category"] = relationship(
        back_populates="category_rules",
    )
