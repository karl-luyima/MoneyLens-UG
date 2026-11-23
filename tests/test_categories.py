
"""Tests for MoneyLens UG category initialization and retraining."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from app.data.system_categories import (
    DEFAULT_CATEGORY_RULES,
    SYSTEM_CATEGORIES,
)
from app.models.category import Category
from app.models.category_correction import CategoryCorrection
from app.models.category_rule import CategoryRule
from app.models.transaction import Transaction
from app.models.user import User
from app.services.category_service import (
    initialize_user_categories,
    seed_default_category_rules,
    seed_system_categories,
)


def test_seed_system_categories(db_session):
    """All predefined system categories should be created."""

    categories = seed_system_categories(db_session)

    assert len(categories) == len(SYSTEM_CATEGORIES)

    category_names = {category.name for category in categories}

    expected_names = {
        category["name"] for category in SYSTEM_CATEGORIES
    }

    assert category_names == expected_names

    assert all(category.is_system for category in categories)
    assert all(category.user_id is None for category in categories)


def test_seed_system_categories_is_idempotent(db_session):
    """Running system category seeding twice should not create duplicates."""

    first_run = seed_system_categories(db_session)
    second_run = seed_system_categories(db_session)

    categories = db_session.scalars(
        select(Category).where(
            Category.is_system.is_(True),
            Category.user_id.is_(None),
        )
    ).all()

    assert len(first_run) == len(SYSTEM_CATEGORIES)
    assert len(second_run) == len(SYSTEM_CATEGORIES)
    assert len(categories) == len(SYSTEM_CATEGORIES)


def test_seed_default_category_rules(db_session, test_user):
    """Default keyword rules should belong to the specified user."""

    seed_system_categories(db_session)

    rules = seed_default_category_rules(
        db=db_session,
        user_id=test_user.id,
    )

    assert len(rules) == len(DEFAULT_CATEGORY_RULES)

    assert all(rule.user_id == test_user.id for rule in rules)
    assert all(rule.is_active for rule in rules)
    assert all(rule.match_field == "counterparty" for rule in rules)

    keywords = {rule.keyword for rule in rules}

    expected_keywords = {
        rule["keyword"] for rule in DEFAULT_CATEGORY_RULES
    }

    assert keywords == expected_keywords


def test_seed_default_category_rules_is_idempotent(
    db_session,
    test_user,
):
    """Running default rule seeding twice should not duplicate rules."""

    seed_system_categories(db_session)

    first_run = seed_default_category_rules(
        db_session,
        test_user.id,
    )

    second_run = seed_default_category_rules(
        db_session,
        test_user.id,
    )

    existing_rules = db_session.scalars(
        select(CategoryRule).where(
            CategoryRule.user_id == test_user.id,
        )
    ).all()

    assert len(first_run) == len(DEFAULT_CATEGORY_RULES)
    assert len(second_run) == 0
    assert len(existing_rules) == len(DEFAULT_CATEGORY_RULES)


def test_users_receive_independent_default_rules(
    db_session,
    test_user,
):
    """Each user should receive their own independent keyword rules."""

    second_user = User(
        email="second_category_user@moneylens.ug",
        hashed_password="synthetic-test-password",
        is_active=True,
    )

    db_session.add(second_user)
    db_session.flush()

    seed_system_categories(db_session)

    seed_default_category_rules(db_session, test_user.id)
    seed_default_category_rules(db_session, second_user.id)

    first_user_rules = db_session.scalars(
        select(CategoryRule).where(
            CategoryRule.user_id == test_user.id,
        )
    ).all()

    second_user_rules = db_session.scalars(
        select(CategoryRule).where(
            CategoryRule.user_id == second_user.id,
        )
    ).all()

    assert len(first_user_rules) == len(DEFAULT_CATEGORY_RULES)
    assert len(second_user_rules) == len(DEFAULT_CATEGORY_RULES)

    first_user_keywords = {rule.keyword for rule in first_user_rules}
    second_user_keywords = {rule.keyword for rule in second_user_rules}

    assert first_user_keywords == second_user_keywords

    assert all(
        rule.user_id == test_user.id for rule in first_user_rules
    )

    assert all(
        rule.user_id == second_user.id for rule in second_user_rules
    )


def test_initialization_preserves_customized_rules(
    db_session,
    test_user,
):
    """Initialization should not overwrite an existing user rule."""

    categories, _ = initialize_user_categories(
        db_session,
        test_user.id,
    )

    transport_category = next(
        category
        for category in categories
        if category.name == "Transport"
    )

    custom_category = Category(
        user_id=test_user.id,
        name="My Travel",
        description="A user-created transport category.",
        is_system=False,
    )

    db_session.add(custom_category)
    db_session.flush()

    # Change the default FARAS rule to a user-selected category.
    faras_rule = db_session.scalar(
        select(CategoryRule).where(
            CategoryRule.user_id == test_user.id,
            CategoryRule.keyword == "FARAS",
        )
    )

    assert faras_rule is not None

    faras_rule.category_id = custom_category.id
    faras_rule.is_active = False

    db_session.flush()

    # Run initialization again.
    initialize_user_categories(db_session, test_user.id)

    # Retrieve the existing customized rule.
    updated_rule = db_session.scalar(
        select(CategoryRule).where(
            CategoryRule.user_id == test_user.id,
            CategoryRule.keyword == "FARAS",
        )
    )

    assert updated_rule is not None
    assert updated_rule.category_id == custom_category.id
    assert updated_rule.is_active is False
    assert updated_rule.category_id != transport_category.id


def create_retraining_correction(db_session, user_id: int) -> None:
    """Create a synthetic transaction correction for endpoint testing."""

    category = db_session.scalar(
        select(Category).where(
            Category.name == "Transport",
            Category.is_system.is_(True),
            Category.user_id.is_(None),
        )
    )

    assert category is not None

    transaction = Transaction(
        user_id=user_id,
        transaction_id=f"API-RETRAIN-{user_id}",
        provider="MTN",
        transaction_type="send_money",
        amount=Decimal("15000.00"),
        timestamp=datetime.now(UTC),
        raw_message="Synthetic FARAS transport payment.",
    )

    db_session.add(transaction)
    db_session.flush()

    correction = CategoryCorrection(
        user_id=user_id,
        transaction_id=transaction.id,
        category_id=category.id,
    )

    db_session.add(correction)
    db_session.flush()


def test_retrain_endpoint_requires_authentication(client):
    """Unauthenticated users must not access model retraining."""

    response = client.post("/api/v1/categories/retrain")

    assert response.status_code == 401


def test_retrain_endpoint_rejects_users_without_corrections(
    client,
    auth_headers,
):
    """The endpoint should return 400 when no corrections exist."""

    response = client.post(
        "/api/v1/categories/retrain",
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "No category corrections found for this user."
    )


def test_retrain_endpoint_trains_personalized_model(
    client,
    db_session,
    test_user,
    auth_headers,
    tmp_path,
    monkeypatch,
):
    """Authenticated users should be able to retrain their own model."""

    from app.ml import retraining

    monkeypatch.setattr(
        retraining,
        "PERSONALIZED_MODEL_DIR",
        tmp_path,
    )

    create_retraining_correction(
        db_session,
        test_user.id,
    )

    response = client.post(
        "/api/v1/categories/retrain",
        headers=auth_headers,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["message"] == (
        "Personalized categorization model trained successfully."
    )
    assert response_data["model_version"] == 1
    assert response_data["corrections_used"] == 1
    assert response_data["training_examples"] == 1301

    model_path = tmp_path / f"user_{test_user.id}_v1.joblib"

    assert model_path.exists()
