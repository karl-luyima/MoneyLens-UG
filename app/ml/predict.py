#This file will 
# load the trained model and predict a category for a transaction description. 
# It will also return the model's confidence score.
"""Prediction utilities for the MoneyLens UG categorization model."""

from pathlib import Path
from typing import Any

import joblib


# Resolve the saved model path.
BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = (
    BASE_DIR / "app" / "ml" / "models" / "transaction_categorizer.joblib"
)

# Load the model only once when this module is imported.
_model: Any = None


def get_model() -> Any:
    """Load and cache the trained categorization model."""

    global _model

    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                "Trained model not found. Run python -m app.ml.train first."
            )

        _model = joblib.load(MODEL_PATH)

    return _model


def predict_category(text: str) -> dict[str, str | float]:
    """Predict a transaction category and its confidence score."""

    if not text or not text.strip():
        raise ValueError("Transaction description cannot be empty.")

    model = get_model()

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
