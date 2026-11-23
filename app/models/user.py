#user account and auth details(someone registered on the app)
#Owns the account and personal financial data such as transactions and uploaded statements


"""User database model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """A registered MoneyLens UG user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
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

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    uploads: Mapped[list["Upload"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    categories: Mapped[list["Category"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    category_rules: Mapped[list["CategoryRule"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    unparsed_messages: Mapped[list["UnparsedMessage"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
