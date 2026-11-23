
# This file will
# load the trained model and predict a category for a transaction description.
# It will also return the model's confidence score.
"""Prediction utilities for the MoneyLens UG categorization model."""

from pathlib import Path
from typing import Any

import joblib

# Resolve the saved model paths.
BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = (
    BASE_DIR / "app" / "ml" / "models" / "transaction_categorizer.joblib"
)
PERSONALIZED_MODEL_DIR = (
    BASE_DIR / "app" / "ml" / "models" / "personalized"
)

# Cache loaded models separately to prevent cross-user model reuse.
_model_cache: dict[str, Any] = {}


def get_model(user_id: int | None = None) -> Any:
    """Load the latest personalized model or the baseline model."""

    model_path = MODEL_PATH

    if user_id is not None:
        personalized_models = list(
            PERSONALIZED_MODEL_DIR.glob(
                f"user_{user_id}_v*.joblib"
            )
        )

        if personalized_models:
            # Select the highest numeric version, not the filename order.
            model_path = max(
                personalized_models,
                key=lambda path: int(
                    path.stem.rsplit("_v", maxsplit=1)[1]
                ),
            )

    cache_key = str(model_path)

    if cache_key not in _model_cache:
        if not model_path.exists():
            raise FileNotFoundError(
                "Trained model not found. Run python -m app.ml.train first."
            )

        _model_cache[cache_key] = joblib.load(model_path)

    return _model_cache[cache_key]


def predict_category(
    text: str,
    user_id: int | None = None,
) -> dict[str, str | float]:
    """Predict a transaction category and its confidence score."""

    if not text or not text.strip():
        raise ValueError("Transaction description cannot be empty.")

    model = get_model(user_id)

    # Predict the most likely category.
    predicted_category = str(model.predict([text])[0])

    # Retrieve the probability assigned to each category.
    probabilities = model.predict_proba([text])[0]

    # Get the probability associated with the predicted category.
    predicted_index = list(model.classes_).index(predicted_category)
    confidence = float(probabilities[predicted_index])

    return {
        "category": predicted_category,
        "confidence": confidence,
    }
