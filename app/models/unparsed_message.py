# Messages that failed parsing with the Phase 1 parser

"""Database model for messages that could not be parsed."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.upload import Upload
from app.models.user import User


class UnparsedMessage(Base):
    """A mobile money message that the parser could not recognise."""

    __tablename__ = "unparsed_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    upload_id: Mapped[int] = mapped_column(
        ForeignKey("uploads.id", ondelete="CASCADE"),
        nullable=False,
    )

    raw_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="unparsed_messages",
    )
    upload: Mapped["Upload"] = relationship(
        back_populates="unparsed_messages",
    )
