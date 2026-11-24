
"""Service for calculating financial insights and detecting anomalies."""

from collections import defaultdict
from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.transaction import Transaction
from app.schemas.insights import (
    AnomalyItem,
    CategoryBreakdownItem,
    CounterpartyItem,
    InsightsSummaryResponse,
    MonthlyTrendItem,
)

INCOME_TYPES = {
    "receive_money",
    "cash_deposit",
}

EXPENSE_TYPES = {
    "send_money",
    "cash_withdrawal",
    "airtime",
    "bill_umeme",
    "bill_nwsc",
    "bill_dstv",
    "bill_ura",
    "bank_transfer",
}

ZERO = Decimal("0.00")
IQR_MULTIPLIER = Decimal("1.5")
MINIMUM_ANOMALY_SAMPLES = 4
UGANDA_TIMEZONE = ZoneInfo("Africa/Kampala")


def calculate_quartile(
    sorted_values: list[Decimal],
    quartile: int,
) -> Decimal:
    """Calculate an interpolated quartile from sorted decimal values."""

    position = (
        Decimal(len(sorted_values) - 1)
        * Decimal(quartile)
        / Decimal(4)
    )

    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)

    fraction = position - Decimal(lower_index)

    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]

    return lower_value + (upper_value - lower_value) * fraction


def detect_anomalies(
    transactions: Sequence[Transaction],
) -> list[AnomalyItem]:
    """Detect unusually large outgoing transactions using IQR per category."""

    transactions_by_category: dict[str, list[Transaction]] = defaultdict(list)

    for transaction in transactions:
        if transaction.transaction_type not in EXPENSE_TYPES:
            continue

        category_name = (
            transaction.category.name
            if transaction.category is not None
            else "Uncategorized"
        )

        transactions_by_category[category_name].append(transaction)

    anomalies: list[AnomalyItem] = []

    for category_name, category_transactions in transactions_by_category.items():
        if len(category_transactions) < MINIMUM_ANOMALY_SAMPLES:
            continue

        amounts = sorted(
            transaction.amount
            for transaction in category_transactions
        )

        q1 = calculate_quartile(amounts, 1)
        q3 = calculate_quartile(amounts, 3)
        iqr = q3 - q1

        lower_bound = q1 - (IQR_MULTIPLIER * iqr)
        upper_bound = q3 + (IQR_MULTIPLIER * iqr)

        for transaction in category_transactions:
            amount = transaction.amount

            if amount < lower_bound:
                reason = (
                    f"Amount is below the category's lower IQR bound "
                    f"of UGX {lower_bound:.2f}."
                )
            elif amount > upper_bound:
                reason = (
                    f"Amount exceeds the category's upper IQR bound "
                    f"of UGX {upper_bound:.2f}."
                )
            else:
                continue

            anomalies.append(
                AnomalyItem(
                    transaction_id=transaction.id,
                    amount=amount,
                    category=category_name,
                    counterparty=transaction.counterparty,
                    timestamp=transaction.timestamp,
                    reason=reason,
                )
            )

    return sorted(
        anomalies,
        key=lambda anomaly: anomaly.amount,
        reverse=True,
    )


def generate_insights_summary(
    db: Session,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> InsightsSummaryResponse:
    """Generate financial insights for one user within an optional date range."""

    query = (
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.user_id == user_id)
    )

    if start_date is not None:
        start_datetime = datetime.combine(
            start_date,
            time.min,
            tzinfo=UGANDA_TIMEZONE,
        )
        query = query.where(Transaction.timestamp >= start_datetime)

    if end_date is not None:
        end_datetime = datetime.combine(
            end_date + timedelta(days=1),
            time.min,
            tzinfo=UGANDA_TIMEZONE,
        )
        query = query.where(Transaction.timestamp < end_datetime)

    transactions = db.scalars(
        query.order_by(Transaction.timestamp.asc())
    ).all()

    total_income = ZERO
    total_expenses = ZERO
    total_fees = ZERO

    monthly_totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "income": ZERO,
            "expenses": ZERO,
        }
    )

    category_totals: dict[str, dict[str, Decimal | int]] = defaultdict(
        lambda: {
            "total_amount": ZERO,
            "transaction_count": 0,
        }
    )

    counterparty_totals: dict[str, dict[str, Decimal | int]] = defaultdict(
        lambda: {
            "total_amount": ZERO,
            "transaction_count": 0,
        }
    )

    for transaction in transactions:
        amount = transaction.amount
        fee = transaction.fee or ZERO
        month = transaction.timestamp.astimezone(
            UGANDA_TIMEZONE
        ).strftime("%Y-%m")

        total_fees += fee

        if transaction.transaction_type in INCOME_TYPES:
            total_income += amount
            monthly_totals[month]["income"] += amount

        elif transaction.transaction_type in EXPENSE_TYPES:
            total_expenses += amount
            monthly_totals[month]["expenses"] += amount

            category_name = (
                transaction.category.name
                if transaction.category is not None
                else "Uncategorized"
            )

            category_totals[category_name]["total_amount"] += amount
            category_totals[category_name]["transaction_count"] += 1

            if transaction.counterparty:
                counterparty = transaction.counterparty.strip()

                if counterparty:
                    counterparty_totals[counterparty]["total_amount"] += amount
                    counterparty_totals[counterparty]["transaction_count"] += 1

    monthly_trend = [
        MonthlyTrendItem(
            month=month,
            income=totals["income"],
            expenses=totals["expenses"],
        )
        for month, totals in sorted(monthly_totals.items())
    ]

    category_breakdown = [
        CategoryBreakdownItem(
            category=category,
            total_amount=Decimal(str(totals["total_amount"])),
            transaction_count=int(totals["transaction_count"]),
        )
        for category, totals in sorted(
            category_totals.items(),
            key=lambda item: item[1]["total_amount"],
            reverse=True,
        )
    ]

    top_counterparties = [
        CounterpartyItem(
            counterparty=counterparty,
            total_amount=Decimal(str(totals["total_amount"])),
            transaction_count=int(totals["transaction_count"]),
        )
        for counterparty, totals in sorted(
            counterparty_totals.items(),
            key=lambda item: item[1]["total_amount"],
            reverse=True,
        )[:5]
    ]

    anomalies = detect_anomalies(transactions)

    return InsightsSummaryResponse(
        total_income=total_income,
        total_expenses=total_expenses,
        total_fees=total_fees,
        monthly_trend=monthly_trend,
        category_breakdown=category_breakdown,
        top_counterparties=top_counterparties,
        anomalies=anomalies,
        transaction_count=len(transactions),
    )
