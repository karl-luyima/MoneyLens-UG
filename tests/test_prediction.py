
"""Tests for the MoneyLens UG ML prediction service."""

import pytest

from app.ml.predict import predict_category


@pytest.mark.parametrize(
    ("message", "expected_category"),
    [
        ("Payment made to FARAS for transport", "Transport"),
        ("Payment made at Carrefour supermarket", "Food & Groceries"),
        ("Purchased airtime worth UGX 10,000", "Airtime & Data"),
        ("Paid monthly UMEME electricity bill", "Utilities"),
        ("Transferred money to another mobile money user", "Transfers"),
        ("Purchased items through Jumia", "Shopping"),
    ],
)
def test_predict_category(message: str, expected_category: str) -> None:
    """Check that the model predicts expected transaction categories."""

    result = predict_category(message)

    assert result["category"] == expected_category
    assert 0.0 <= result["confidence"] <= 1.0


def test_predict_category_rejects_empty_text() -> None:
    """Ensure empty transaction descriptions are rejected."""

    with pytest.raises(ValueError, match="cannot be empty"):
        predict_category("")


def test_predict_category_rejects_whitespace() -> None:
    """Ensure whitespace-only descriptions are rejected."""

    with pytest.raises(ValueError, match="cannot be empty"):
        predict_category("   ")
