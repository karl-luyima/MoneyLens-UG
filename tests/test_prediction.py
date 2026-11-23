
"""Tests for the MoneyLens UG ML prediction service."""

import joblib
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline

from app.ml import predict


@pytest.fixture
def fake_model():
    """Create a simple model for testing personalized predictions."""

    return Pipeline(
        [
            ("vectorizer", CountVectorizer()),
            (
                "classifier",
                DummyClassifier(strategy="constant", constant="Transport"),
            ),
        ]
    ).fit(
        ["synthetic transport payment"],
        ["Transport"],
    )


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

    result = predict.predict_category(message)

    assert result["category"] == expected_category
    assert 0.0 <= result["confidence"] <= 1.0


def test_predict_category_rejects_empty_text() -> None:
    """Ensure empty transaction descriptions are rejected."""

    with pytest.raises(ValueError, match="cannot be empty"):
        predict.predict_category("")


def test_predict_category_rejects_whitespace() -> None:
    """Ensure whitespace-only descriptions are rejected."""

    with pytest.raises(ValueError, match="cannot be empty"):
        predict.predict_category("   ")


def test_personalized_model_is_selected(
    tmp_path,
    monkeypatch,
    fake_model,
) -> None:
    """Ensure a user receives their own personalized model."""

    monkeypatch.setattr(
        predict,
        "PERSONALIZED_MODEL_DIR",
        tmp_path,
    )
    monkeypatch.setattr(predict, "_model_cache", {})

    model_path = tmp_path / "user_101_v1.joblib"
    joblib.dump(fake_model, model_path)

    result = predict.predict_category(
        "synthetic transport payment",
        user_id=101,
    )

    assert result["category"] == "Transport"


def test_latest_personalized_model_is_selected(
    tmp_path,
    monkeypatch,
    fake_model,
) -> None:
    """Ensure the highest numeric model version is selected."""

    monkeypatch.setattr(
        predict,
        "PERSONALIZED_MODEL_DIR",
        tmp_path,
    )
    monkeypatch.setattr(predict, "_model_cache", {})

    # Both models predict Transport, but their versions are selected
    # by numeric version rather than filename order.
    joblib.dump(fake_model, tmp_path / "user_102_v2.joblib")
    joblib.dump(fake_model, tmp_path / "user_102_v10.joblib")

    selected_model = predict.get_model(user_id=102)

    assert selected_model is not None
    assert str(
        tmp_path / "user_102_v10.joblib"
    ) in predict._model_cache


def test_personalized_models_are_isolated_by_user(
    tmp_path,
    monkeypatch,
    fake_model,
) -> None:
    """Ensure different users load separate personalized models."""

    monkeypatch.setattr(
        predict,
        "PERSONALIZED_MODEL_DIR",
        tmp_path,
    )
    monkeypatch.setattr(predict, "_model_cache", {})

    joblib.dump(fake_model, tmp_path / "user_103_v1.joblib")
    joblib.dump(fake_model, tmp_path / "user_104_v1.joblib")

    first_model = predict.get_model(user_id=103)
    second_model = predict.get_model(user_id=104)

    assert first_model is not second_model
    assert len(predict._model_cache) == 2


def test_missing_personalized_model_uses_baseline(
    tmp_path,
    monkeypatch,
) -> None:
    """Ensure users without personalized models use the baseline model."""

    monkeypatch.setattr(
        predict,
        "PERSONALIZED_MODEL_DIR",
        tmp_path,
    )
    monkeypatch.setattr(predict, "_model_cache", {})

    baseline_model = predict.get_model(user_id=999999)

    assert baseline_model is not None
    assert str(predict.MODEL_PATH) in predict._model_cache
