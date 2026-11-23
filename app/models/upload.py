# uploaded statements and processing status.
# Imported messages or files

"""Uploaded mobile money data database model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.unparsed_message import UnparsedMessage
    from app.models.user import User


class Upload(Base):
    """Tracks a user's imported mobile money messages or files."""

    __tablename__ = "uploads"

    __table_args__ = (Index("ix_uploads_user_created_at", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    total_messages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    parsed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    duplicate_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    unparsed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="completed",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="uploads",
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="upload",
    )
    unparsed_messages: Mapped[list["UnparsedMessage"]] = relationship(
        back_populates="upload",
        cascade="all, delete-orphan",
    )
