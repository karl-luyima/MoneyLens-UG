
"""API endpoints for retrieving mobile money transactions."""

# This endpoint supports filtering, sorting and pagination.
# Every query is restricted to the authenticated user's records.

import math
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import (
    TransactionListResponse,
    TransactionResponse,
)

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.get(
    "",
    response_model=TransactionListResponse,
)
def get_transactions(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    provider: str | None = None,
    transaction_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    sort_by: Literal["timestamp", "amount", "created_at"] = "timestamp",
    sort_order: Literal["asc", "desc"] = "desc",
) -> TransactionListResponse:
    """Retrieve transactions belonging to the authenticated user."""

    # Prevent invalid date and amount ranges.
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from cannot be later than date_to.",
        )

    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_amount cannot be greater than max_amount.",
        )

    # Every transaction query must be scoped to the current user.
    base_query = select(Transaction).where(Transaction.user_id == current_user.id)

    if provider:
        normalised_provider = provider.strip().upper()

        if normalised_provider not in {"MTN", "AIRTEL"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="provider must be MTN or AIRTEL.",
            )

        base_query = base_query.where(Transaction.provider == normalised_provider)

    if transaction_type:
        base_query = base_query.where(
            Transaction.transaction_type == transaction_type.strip().lower()
        )

    if date_from:
        base_query = base_query.where(Transaction.timestamp >= date_from)

    if date_to:
        base_query = base_query.where(Transaction.timestamp <= date_to)

    if min_amount is not None:
        base_query = base_query.where(Transaction.amount >= min_amount)

    if max_amount is not None:
        base_query = base_query.where(Transaction.amount <= max_amount)

    # Count matching records before pagination.
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

    # Apply sorting using an explicitly allowed column.
    sort_column = getattr(Transaction, sort_by)

    if sort_order == "asc":
        base_query = base_query.order_by(sort_column.asc())
    else:
        base_query = base_query.order_by(sort_column.desc())

    # Apply pagination.
    transactions = db.scalars(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).all()

    return TransactionListResponse(
        items=[
            TransactionResponse.model_validate(transaction)
            for transaction in transactions
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )
