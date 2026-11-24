
"""Tests for financial insights calculations and anomaly detection."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.services.insights_service import (
    calculate_quartile,
    detect_anomalies,
    generate_insights_summary,
)


def create_category(db_session: Session, name: str) -> Category:
    """Create a category for insights tests."""

    category = Category(
        name=name,
        description=f"{name} test category",
        is_system=True,
        user_id=None,
    )

    db_session.add(category)
    db_session.flush()

    return category


def create_transaction(
    db_session: Session,
    user: User,
    category: Category | None,
    amount: str,
    transaction_type: str,
    day: int,
    fee: str = "0.00",
    counterparty: str | None = None,
) -> Transaction:
    """Create a transaction with predictable test values."""

    transaction = Transaction(
        user_id=user.id,
        category_id=category.id if category else None,
        provider="MTN",
        transaction_type=transaction_type,
        amount=Decimal(amount),
        fee=Decimal(fee),
        counterparty=counterparty,
        timestamp=datetime(
            2026,
            11,
            day,
            10,
            0,
            tzinfo=UTC,
        ),
        raw_message="Synthetic test transaction",
    )

    db_session.add(transaction)
    db_session.flush()

    return transaction


def test_calculate_quartile():
    """Quartile calculation should interpolate between values."""

    values = [
        Decimal("100"),
        Decimal("200"),
        Decimal("300"),
        Decimal("400"),
        Decimal("500"),
    ]

    assert calculate_quartile(values, 1) == Decimal("200")
    assert calculate_quartile(values, 3) == Decimal("400")


def test_insights_summary_calculates_financial_totals(
    db_session: Session,
    test_user: User,
):
    """Income, expenses, fees and transaction counts should be correct."""

    category = create_category(db_session, "Food & Groceries")

    create_transaction(
        db_session,
        test_user,
        None,
        "50000",
        "receive_money",
        1,
        fee="0",
        counterparty="Employer",
    )

    create_transaction(
        db_session,
        test_user,
        category,
        "10000",
        "send_money",
        2,
        fee="500",
        counterparty="Carrefour",
    )

    create_transaction(
        db_session,
        test_user,
        category,
        "5000",
        "airtime",
        3,
        fee="100",
        counterparty="MTN",
    )

    summary = generate_insights_summary(
        db=db_session,
        user_id=test_user.id,
    )

    assert summary.total_income == Decimal("50000")
    assert summary.total_expenses == Decimal("15000")
    assert summary.total_fees == Decimal("600")
    assert summary.transaction_count == 3


def test_insights_summary_groups_monthly_totals(
    db_session: Session,
    test_user: User,
):
    """Transactions should be grouped by calendar month."""

    create_transaction(
        db_session,
        test_user,
        None,
        "30000",
        "receive_money",
        1,
    )

    create_transaction(
        db_session,
        test_user,
        None,
        "10000",
        "send_money",
        15,
    )

    summary = generate_insights_summary(
        db=db_session,
        user_id=test_user.id,
    )

    assert len(summary.monthly_trend) == 1

    november = summary.monthly_trend[0]

    assert november.month == "2026-11"
    assert november.income == Decimal("30000")
    assert november.expenses == Decimal("10000")


def test_insights_summary_groups_categories_and_counterparties(
    db_session: Session,
    test_user: User,
):
    """Outgoing transactions should be grouped by category and counterparty."""

    category = create_category(db_session, "Food & Groceries")

    create_transaction(
        db_session,
        test_user,
        category,
        "20000",
        "send_money",
        1,
        counterparty="Carrefour",
    )

    create_transaction(
        db_session,
        test_user,
        category,
        "15000",
        "send_money",
        2,
        counterparty="Carrefour",
    )

    create_transaction(
        db_session,
        test_user,
        category,
        "5000",
        "airtime",
        3,
        counterparty="MTN",
    )

    summary = generate_insights_summary(
        db=db_session,
        user_id=test_user.id,
    )

    assert len(summary.category_breakdown) == 1

    food = summary.category_breakdown[0]

    assert food.category == "Food & Groceries"
    assert food.total_amount == Decimal("40000")
    assert food.transaction_count == 3

    assert summary.top_counterparties[0].counterparty == "Carrefour"
    assert summary.top_counterparties[0].total_amount == Decimal("35000")
    assert summary.top_counterparties[0].transaction_count == 2


def test_detect_anomalies_identifies_unusually_large_transaction(
    db_session: Session,
    test_user: User,
):
    """An unusually large transaction should be flagged by IQR."""

    category = create_category(db_session, "Shopping")

    amounts = ["100", "110", "120", "130", "10000"]

    for day, amount in enumerate(amounts, start=1):
        create_transaction(
            db_session,
            test_user,
            category,
            amount,
            "send_money",
            day,
            counterparty="Shop",
        )

    transactions = (
        db_session.query(Transaction)
        .filter(Transaction.user_id == test_user.id)
        .all()
    )

    anomalies = detect_anomalies(transactions)

    assert len(anomalies) == 1
    assert anomalies[0].amount == Decimal("10000")
    assert anomalies[0].category == "Shopping"
    assert "upper IQR bound" in anomalies[0].reason


def test_detect_anomalies_ignores_categories_with_too_few_transactions(
    db_session: Session,
    test_user: User,
):
    """Categories with fewer than four transactions should not be flagged."""

    category = create_category(db_session, "Transport")

    for day, amount in enumerate(["100", "200", "300"], start=1):
        create_transaction(
            db_session,
            test_user,
            category,
            amount,
            "send_money",
            day,
        )

    transactions = (
        db_session.query(Transaction)
        .filter(Transaction.user_id == test_user.id)
        .all()
    )

    assert detect_anomalies(transactions) == []


def test_insights_summary_returns_empty_results_for_user_without_transactions(
    db_session: Session,
    test_user: User,
):
    """A user without transactions should receive zero totals and empty lists."""

    summary = generate_insights_summary(
        db=db_session,
        user_id=test_user.id,
    )

    assert summary.total_income == Decimal("0.00")
    assert summary.total_expenses == Decimal("0.00")
    assert summary.total_fees == Decimal("0.00")
    assert summary.transaction_count == 0
    assert summary.monthly_trend == []
    assert summary.category_breakdown == []
    assert summary.top_counterparties == []
    assert summary.anomalies == []


def test_insights_summary_only_includes_authenticated_users_transactions(
    db_session: Session,
    test_user: User,
):
    """Insights must never include another user's transactions."""

    category = create_category(db_session, "Shopping")

    create_transaction(
        db_session,
        test_user,
        category,
        "10000",
        "send_money",
        1,
    )

    another_user = User(
        email="another_pytest_user@moneylens.ug",
        hashed_password="test-password-hash",
        is_active=True,
    )

    db_session.add(another_user)
    db_session.flush()

    create_transaction(
        db_session,
        another_user,
        category,
        "90000",
        "receive_money",
        2,
    )

    summary = generate_insights_summary(
        db=db_session,
        user_id=test_user.id,
    )

    assert summary.transaction_count == 1
    assert summary.total_income == Decimal("0.00")
    assert summary.total_expenses == Decimal("10000")

def test_insights_summary_filters_inclusive_date_range(
    db_session: Session,
    test_user: User,
):
    """Both boundary dates should be included in the selected date range."""

    for day, amount in [
        (1, "1000"),
        (2, "2000"),
        (3, "3000"),
        (4, "4000"),
        (5, "5000"),
    ]:
        create_transaction(
            db_session,
            test_user,
            None,
            amount,
            "send_money",
            day,
        )

    summary = generate_insights_summary(
        db=db_session,
        user_id=test_user.id,
        start_date=datetime(2026, 11, 2).date(),
        end_date=datetime(2026, 11, 4).date(),
    )

    assert summary.transaction_count == 3
    assert summary.total_expenses == Decimal("9000")


def test_insights_summary_filters_from_start_date(
    db_session: Session,
    test_user: User,
):
    """Transactions before the start date should be excluded."""

    for day, amount in [
        (1, "1000"),
        (2, "2000"),
        (3, "3000"),
    ]:
        create_transaction(
            db_session,
            test_user,
            None,
            amount,
            "send_money",
            day,
        )

    summary = generate_insights_summary(
        db=db_session,
        user_id=test_user.id,
        start_date=datetime(2026, 11, 2).date(),
    )

    assert summary.transaction_count == 2
    assert summary.total_expenses == Decimal("5000")


def test_insights_summary_filters_until_end_date(
    db_session: Session,
    test_user: User,
):
    """Transactions after the end date should be excluded."""

    for day, amount in [
        (1, "1000"),
        (2, "2000"),
        (3, "3000"),
    ]:
        create_transaction(
            db_session,
            test_user,
            None,
            amount,
            "send_money",
            day,
        )

    summary = generate_insights_summary(
        db=db_session,
        user_id=test_user.id,
        end_date=datetime(2026, 11, 2).date(),
    )

    assert summary.transaction_count == 2
    assert summary.total_expenses == Decimal("3000")
