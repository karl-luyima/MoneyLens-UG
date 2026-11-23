# This module will:
# 1. Load the synthetic labelled dataset.
# 2. Split it into training and testing sets.
# 3. Load the trained model.
# 4. Evaluate the model on the test set.
# 5. Generate precision, recall, F1-score, and a confusion matrix.

"""Evaluate the MoneyLens UG transaction categorization model."""

import json
from pathlib import Path

import joblib
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split


# Resolve project paths.
BASE_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = BASE_DIR / "data" / "synthetic" / "category_training_data.json"
MODEL_PATH = (
    BASE_DIR / "app" / "ml" / "models" / "transaction_categorizer.joblib"
)
REPORT_DIR = BASE_DIR / "docs"
REPORT_PATH = REPORT_DIR / "category_model_evaluation.json"


def load_test_data() -> tuple[list[str], list[str]]:
    """Load the same held-out examples used during training."""

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    texts = [item["text"].strip() for item in dataset]
    labels = [item["category"].strip() for item in dataset]

    x_train, x_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    return x_test, y_test


def evaluate_model() -> None:
    """Evaluate the trained model and save its performance report."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Trained model not found. Run python -m app.ml.train first."
        )

    model = joblib.load(MODEL_PATH)

    x_test, y_test = load_test_data()

    predictions = model.predict(x_test)

    # Generate precision, recall, F1-score and support for every category.
    report = classification_report(
        y_test,
        predictions,
        output_dict=True,
        zero_division=0,
    )

    # Generate a confusion matrix using the model's category order.
    categories = list(model.classes_)

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=categories,
    )

    evaluation_results = {
        "test_examples": len(x_test),
        "categories": categories,
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(evaluation_results, file, indent=4)

    print("\nMODEL EVALUATION")
    print("----------------")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    print("Confusion Matrix:")
    print(matrix)

    print(f"\nEvaluation report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    evaluate_model()
