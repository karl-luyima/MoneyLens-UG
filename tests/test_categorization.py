
"""Tests for automatic mobile money transaction categorization."""

from datetime import UTC, datetime
from decimal import Decimal

from app.models.category import Category
from app.models.category_rule import CategoryRule
from app.models.transaction import Transaction
from app.models.user import User
from app.services.categorization_service import categorize_transaction
from app.services.category_service import initialize_user_categories


def create_test_transaction(
    user_id: int,
    transaction_type: str = "unknown_type",
    counterparty: str | None = None,
) -> Transaction:
    """Create a synthetic transaction for categorization tests."""

    return Transaction(
        user_id=user_id,
        transaction_id=None,
        provider="MTN",
        transaction_type=transaction_type,
        amount=Decimal("10000.00"),
        fee=Decimal("500.00"),
        balance_after=Decimal("50000.00"),
        counterparty=counterparty,
        timestamp=datetime(2026, 11, 23, 12, 0, tzinfo=UTC),
        raw_message="Synthetic transaction for categorization testing.",
    )


def test_keyword_rule_takes_priority_over_transaction_type_mapping(
    db_session,
    test_user,
):
    """Merchant-specific keyword rules should override general type mappings."""

    initialize_user_categories(db_session, test_user.id)

    transaction = create_test_transaction(
        user_id=test_user.id,
        transaction_type="send_money",
        counterparty="FARAS",
    )

    category_id = categorize_transaction(db_session, transaction)

    transport_category = db_session.query(Category).filter_by(
        name="Transport",
        is_system=True,
        user_id=None,
    ).one()

    assert category_id == transport_category.id


def test_transaction_type_mapping_is_used_as_fallback(
    db_session,
    test_user,
):
    """Transaction-type mappings should apply when no keyword rule matches."""

    initialize_user_categories(db_session, test_user.id)

    transaction = create_test_transaction(
        user_id=test_user.id,
        transaction_type="send_money",
        counterparty="UNKNOWN SYNTHETIC MERCHANT",
    )

    category_id = categorize_transaction(db_session, transaction)

    transfers_category = db_session.query(Category).filter_by(
        name="Transfers",
        is_system=True,
        user_id=None,
    ).one()

    assert category_id == transfers_category.id


def test_faras_keyword_is_categorized_as_transport(
    db_session,
    test_user,
):
    """FARAS transactions should be classified as Transport."""

    initialize_user_categories(db_session, test_user.id)

    transaction = create_test_transaction(
        user_id=test_user.id,
        counterparty="FARAS",
    )

    category_id = categorize_transaction(db_session, transaction)

    transport_category = db_session.query(Category).filter_by(
        name="Transport",
        is_system=True,
        user_id=None,
    ).one()

    assert category_id == transport_category.id


def test_carrefour_keyword_is_categorized_as_food_and_groceries(
    db_session,
    test_user,
):
    """Carrefour transactions should be classified as Food & Groceries."""

    initialize_user_categories(db_session, test_user.id)

    transaction = create_test_transaction(
        user_id=test_user.id,
        transaction_type="send_money",
        counterparty="CARREFOUR KAMPALA",
    )

    category_id = categorize_transaction(db_session, transaction)

    category = db_session.query(Category).filter_by(
        name="Food & Groceries",
        is_system=True,
        user_id=None,
    ).one()

    assert category_id == category.id


def test_bolt_keyword_is_categorized_as_transport(
    db_session,
    test_user,
):
    """Bolt transactions should be classified as Transport."""

    initialize_user_categories(db_session, test_user.id)

    transaction = create_test_transaction(
        user_id=test_user.id,
        transaction_type="send_money",
        counterparty="BOLT RIDE",
    )

    category_id = categorize_transaction(db_session, transaction)

    category = db_session.query(Category).filter_by(
        name="Transport",
        is_system=True,
        user_id=None,
    ).one()

    assert category_id == category.id


def test_inactive_keyword_rules_are_ignored(
    db_session,
    test_user,
):
    """Inactive merchant rules should not categorize transactions."""

    initialize_user_categories(db_session, test_user.id)

    faras_rule = db_session.query(CategoryRule).filter_by(
        user_id=test_user.id,
        keyword="FARAS",
    ).one()

    faras_rule.is_active = False
    db_session.flush()

    transaction = create_test_transaction(
        user_id=test_user.id,
        counterparty="FARAS",
    )

    category_id = categorize_transaction(db_session, transaction)

    assert category_id is None


def test_keyword_matching_is_case_insensitive(
    db_session,
    test_user,
):
    """Keyword matching should ignore uppercase and lowercase differences."""

    initialize_user_categories(db_session, test_user.id)

    transaction = create_test_transaction(
        user_id=test_user.id,
        counterparty="payment to faras services",
    )

    category_id = categorize_transaction(db_session, transaction)

    transport_category = db_session.query(Category).filter_by(
        name="Transport",
        is_system=True,
        user_id=None,
    ).one()

    assert category_id == transport_category.id


def test_longest_matching_keyword_wins(
    db_session,
    test_user,
):
    """The longest matching keyword should take priority."""

    initialize_user_categories(db_session, test_user.id)

    custom_category = Category(
        user_id=test_user.id,
        name="Special Transport",
        description="Synthetic custom category for testing.",
        is_system=False,
    )

    db_session.add(custom_category)
    db_session.flush()

    longer_rule = CategoryRule(
        user_id=test_user.id,
        category_id=custom_category.id,
        keyword="FARAS EXPRESS",
        match_field="counterparty",
        is_active=True,
    )

    db_session.add(longer_rule)
    db_session.flush()

    transaction = create_test_transaction(
        user_id=test_user.id,
        counterparty="FARAS EXPRESS KAMPALA",
    )

    category_id = categorize_transaction(db_session, transaction)

    assert category_id == custom_category.id


def test_unmatched_transaction_remains_uncategorized(
    db_session,
    test_user,
):
    """Transactions without a matching type or keyword remain uncategorized."""

    initialize_user_categories(db_session, test_user.id)

    transaction = create_test_transaction(
        user_id=test_user.id,
        counterparty="UNKNOWN SYNTHETIC MERCHANT",
    )

    category_id = categorize_transaction(db_session, transaction)

    assert category_id is None


def test_user_cannot_use_another_users_private_category(
    db_session,
    test_user,
):
    """Rules linked to another user's private category must be ignored."""

    initialize_user_categories(db_session, test_user.id)

    second_user = User(
        email="foreign_category_user@moneylens.ug",
        hashed_password="synthetic-test-password",
        is_active=True,
    )

    db_session.add(second_user)
    db_session.flush()

    foreign_category = Category(
        user_id=second_user.id,
        name="Private Category",
        description="Belongs to another synthetic user.",
        is_system=False,
    )

    db_session.add(foreign_category)
    db_session.flush()

    # Simulate an invalid cross-user category assignment.
    foreign_rule = CategoryRule(
        user_id=test_user.id,
        category_id=foreign_category.id,
        keyword="FOREIGN MERCHANT",
        match_field="counterparty",
        is_active=True,
    )

    db_session.add(foreign_rule)
    db_session.flush()

    transaction = create_test_transaction(
        user_id=test_user.id,
        counterparty="FOREIGN MERCHANT",
    )

    category_id = categorize_transaction(db_session, transaction)

    assert category_id is None
