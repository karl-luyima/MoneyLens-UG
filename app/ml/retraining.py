#This service will 
# retrieve a user's saved corrections, 
# combine them with the original synthetic dataset, 
# train a new model, 
#  save it under that user's ID.


"""Retrain personalized transaction categorization models."""

from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.train import load_training_data
from app.models.category import Category
from app.models.category_correction import CategoryCorrection
from app.models.transaction import Transaction

# Resolve the personalized model directory.
BASE_DIR = Path(__file__).resolve().parents[2]
PERSONALIZED_MODEL_DIR = (
    BASE_DIR / "app" / "ml" / "models" / "personalized"
)


def build_personalized_model() -> Pipeline:
    """Create a TF-IDF and Logistic Regression pipeline."""

    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    strip_accents="unicode",
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ]
    )


def get_next_model_version(user_id: int) -> int:
    """Determine the next model version for a user."""

    existing_models = list(
        PERSONALIZED_MODEL_DIR.glob(
            f"user_{user_id}_v*.joblib"
        )
    )

    versions = []

    for model_path in existing_models:
        try:
            version = int(
                model_path.stem.rsplit("_v", maxsplit=1)[1]
            )
            versions.append(version)
        except (IndexError, ValueError):
            continue

    return max(versions, default=0) + 1


def retrain_user_model(
    db: Session,
    user_id: int,
) -> dict[str, int | str]:
    """Train and save a personalized model using a user's corrections."""

    # Load the original synthetic training examples.
    texts, labels = load_training_data()

    # Retrieve only corrections belonging to this user.
    correction_query = (
        select(Transaction.raw_message, Category.name)
        .join(
            CategoryCorrection,
            CategoryCorrection.transaction_id == Transaction.id,
        )
        .join(
            Category,
            CategoryCorrection.category_id == Category.id,
        )
        .where(
            CategoryCorrection.user_id == user_id,
            Transaction.user_id == user_id,
        )
        .order_by(CategoryCorrection.id.asc())
    )

    corrections = db.execute(correction_query).all()

    if not corrections:
        raise ValueError(
            "No category corrections found for this user."
        )

    # Add the user's corrected transactions to the training dataset.
    for raw_message, category_name in corrections:
        if raw_message and raw_message.strip():
            texts.append(raw_message.strip())
            labels.append(category_name)

    # Train a personalized model.
    model = build_personalized_model()
    model.fit(texts, labels)

    # Generate a new version without overwriting previous versions.
    version = get_next_model_version(user_id)

    PERSONALIZED_MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_path = PERSONALIZED_MODEL_DIR / (
        f"user_{user_id}_v{version}.joblib"
    )

    # Save atomically to avoid leaving a partially written model.
    temporary_path = model_path.with_suffix(".tmp")

    try:
        joblib.dump(model, temporary_path)
        temporary_path.replace(model_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    return {
        "user_id": user_id,
        "model_version": version,
        "corrections_used": len(corrections),
        "training_examples": len(texts),
        "model_path": str(model_path),
    }
