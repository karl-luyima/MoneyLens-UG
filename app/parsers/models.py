"""Pydantic models used by the mobile money parsing engine."""

# This file defines the structure of successful and unsuccessful parsing results.

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Provider = Literal["MTN", "AIRTEL"]

TransactionType = Literal[
    "send_money",
    "receive_money",
    "cash_withdrawal",
    "cash_deposit",
    "airtime",
    "bill_umeme",
    "bill_nwsc",
    "bill_dstv",
    "bill_ura",
    "bank_transfer",
]


class ParsedTransaction(BaseModel):
    """A successfully parsed mobile money transaction."""

    model_config = ConfigDict(str_strip_whitespace=True)

    type: TransactionType
    amount: Decimal = Field(gt=0)
    fee: Decimal | None = Field(default=None, ge=0)
    counterparty: str | None = None
    balance_after: Decimal | None = Field(default=None, ge=0)
    transaction_id: str
    timestamp: datetime
    provider: Provider


class UnparsedResult(BaseModel):
    """A message that could not be parsed, with an explanation."""

    raw_message: str
    provider: Provider | None = None
    reason: str
