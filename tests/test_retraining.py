
"""Tests for personalized MoneyLens UG model retraining."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.ml import retraining
from app.models.category import Category
from app.models.category_correction import CategoryCorrection
from app.models.transaction import Transaction
from app.models.user import User
from app.services.category_service import initialize_user_categories


def create_category_correction(db_session, user_id: int) -> None:
    """Create a synthetic transaction and its category correction."""

    # Find the shared system Transport category.
    category = db_session.scalar(
        select(Category).where(
            Category.name == "Transport",
            Category.is_system.is_(True),
            Category.user_id.is_(None),
        )
    )

    assert category is not None

    # Create a synthetic transaction belonging to the user.
    transaction = Transaction(
        user_id=user_id,
        transaction_id=f"TEST-RETRAIN-{user_id}",
        provider="MTN",
        transaction_type="send_money",
        amount=Decimal("15000.00"),
        timestamp=datetime.now(UTC),
        raw_message=(
            "You paid FARAS UGX 15,000 for transport. "
            "Transaction reference TEST-RETRAIN."
        ),
    )

    db_session.add(transaction)
    db_session.flush()

    # Save the user's corrected category.
    correction = CategoryCorrection(
        user_id=user_id,
        transaction_id=transaction.id,
        category_id=category.id,
    )

    db_session.add(correction)
    db_session.flush()


def test_retraining_fails_without_corrections(
    db_session,
    test_user,
    tmp_path,
    monkeypatch,
) -> None:
    """Ensure users cannot retrain without saved corrections."""

    monkeypatch.setattr(
        retraining,
        "PERSONALIZED_MODEL_DIR",
        tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="No category corrections found",
    ):
        retraining.retrain_user_model(
            db=db_session,
            user_id=test_user.id,
        )


def test_user_model_is_trained_and_saved(
    db_session,
    test_user,
    tmp_path,
    monkeypatch,
) -> None:
    """Ensure a personalized model is trained and saved successfully."""

    initialize_user_categories(
        db=db_session,
        user_id=test_user.id,
    )

    create_category_correction(
        db_session,
        test_user.id,
    )

    monkeypatch.setattr(
        retraining,
        "PERSONALIZED_MODEL_DIR",
        tmp_path,
    )

    result = retraining.retrain_user_model(
        db=db_session,
        user_id=test_user.id,
    )

    assert result["user_id"] == test_user.id
    assert result["model_version"] == 1
    assert result["corrections_used"] == 1
    assert result["training_examples"] == 1301

    model_path = (
        tmp_path / f"user_{test_user.id}_v1.joblib"
    )

    assert model_path.exists()


def test_model_version_increments_on_retraining(
    db_session,
    test_user,
    tmp_path,
    monkeypatch,
) -> None:
    """Ensure retraining creates a new version instead of overwriting."""

    initialize_user_categories(
        db=db_session,
        user_id=test_user.id,
    )

    create_category_correction(
        db_session,
        test_user.id,
    )

    monkeypatch.setattr(
        retraining,
        "PERSONALIZED_MODEL_DIR",
        tmp_path,
    )

    first_result = retraining.retrain_user_model(
        db=db_session,
        user_id=test_user.id,
    )

    second_result = retraining.retrain_user_model(
        db=db_session,
        user_id=test_user.id,
    )

    assert first_result["model_version"] == 1
    assert second_result["model_version"] == 2

    assert (
        tmp_path / f"user_{test_user.id}_v1.joblib"
    ).exists()

    assert (
        tmp_path / f"user_{test_user.id}_v2.joblib"
    ).exists()


def test_users_cannot_retrain_using_another_users_corrections(
    db_session,
    test_user,
    tmp_path,
    monkeypatch,
) -> None:
    """Ensure retraining uses only the authenticated user's corrections."""

    initialize_user_categories(
        db=db_session,
        user_id=test_user.id,
    )

    # Create a second synthetic user.
    another_user = User(
        email="another_retraining_user@moneylens.ug",
        hashed_password="synthetic_test_password",
        is_active=True,
    )

    db_session.add(another_user)
    db_session.flush()

    initialize_user_categories(
        db=db_session,
        user_id=another_user.id,
    )

    # Only the second user has a saved correction.
    create_category_correction(
        db_session,
        another_user.id,
    )

    monkeypatch.setattr(
        retraining,
        "PERSONALIZED_MODEL_DIR",
        tmp_path,
    )

    # The first user must not access the second user's corrections.
    with pytest.raises(
        ValueError,
        match="No category corrections found",
    ):
        retraining.retrain_user_model(
            db=db_session,
            user_id=test_user.id,
        )

    # The second user can train using their own correction.
    result = retraining.retrain_user_model(
        db=db_session,
        user_id=another_user.id,
    )

    assert result["user_id"] == another_user.id
    assert result["corrections_used"] == 1
    assert result["model_version"] == 1
