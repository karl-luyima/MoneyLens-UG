# This module will:
# 1. Load the synthetic labelled dataset.
# 2. Split it into training and testing sets.
# 3. Convert text into TF-IDF features.
# 4. Train a Logistic Regression classifier.
# 5. Save the trained model for later use.


"""Train a TF-IDF and Logistic Regression transaction categorization model."""

import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


# Resolve project paths independently of the working directory.
BASE_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = BASE_DIR / "data" / "synthetic" / "category_training_data.json"
MODEL_DIR = BASE_DIR / "app" / "ml" / "models"
MODEL_PATH = MODEL_DIR / "transaction_categorizer.joblib"


def load_training_data() -> tuple[list[str], list[str]]:
    """Load transaction descriptions and their category labels."""

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    texts = [item["text"].strip() for item in dataset]
    labels = [item["category"].strip() for item in dataset]

    if not texts or len(texts) != len(labels):
        raise ValueError("The training dataset is empty or invalid.")

    if any(not text for text in texts) or any(not label for label in labels):
        raise ValueError("Training examples must have text and category labels.")

    return texts, labels


def train_model() -> Pipeline:
    """Train and save the transaction categorization model."""

    texts, labels = load_training_data()

    # Keep examples from every category represented in both datasets.
    x_train, _, y_train, _ = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    # Combine text vectorization and classification into one pipeline.
    model = Pipeline(
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

    # Fit the model using the training examples.
    model.fit(x_train, y_train)

    # Save the trained model.
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"Training examples: {len(x_train)}")
    print(f"Categories learned: {len(model.classes_)}")
    print(f"Model saved to: {MODEL_PATH}")

    return model


if __name__ == "__main__":
    train_model()
