"""Pydantic schemas for mobile money transactions."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TransactionResponse(BaseModel):
    """Details of a successfully parsed mobile money transaction."""

    id: int
    user_id: int
    upload_id: int | None
    category_id: int | None
    transaction_id: str | None
    provider: str
    transaction_type: str
    amount: Decimal
    fee: Decimal | None
    balance_after: Decimal | None
    counterparty: str | None
    timestamp: datetime
    raw_message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    """Paginated transaction listing response."""

    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    pages: int
