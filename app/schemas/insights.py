
"""Pydantic schemas for financial insights and anomaly detection."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class MonthlyTrendItem(BaseModel):
    """Income and expenditure totals for one calendar month."""

    month: str
    income: Decimal
    expenses: Decimal


class CategoryBreakdownItem(BaseModel):
    """Transaction totals grouped by category."""

    category: str
    total_amount: Decimal
    transaction_count: int


class CounterpartyItem(BaseModel):
    """Spending totals grouped by transaction counterparty."""

    counterparty: str
    total_amount: Decimal
    transaction_count: int


class AnomalyItem(BaseModel):
    """A transaction identified as an unusual financial activity."""

    transaction_id: int
    amount: Decimal
    category: str
    counterparty: str | None
    timestamp: datetime
    reason: str


class InsightsSummaryResponse(BaseModel):
    """Complete financial insights summary for an authenticated user."""

    total_income: Decimal
    total_expenses: Decimal
    total_fees: Decimal
    monthly_trend: list[MonthlyTrendItem]
    category_breakdown: list[CategoryBreakdownItem]
    top_counterparties: list[CounterpartyItem]
    anomalies: list[AnomalyItem]
    transaction_count: int
