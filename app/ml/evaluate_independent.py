
"""Evaluate the MoneyLens UG model on independent synthetic messages."""

import json
from pathlib import Path

import joblib
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

# Resolve project paths.
BASE_DIR = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "independent_test_data.json"
)

MODEL_PATH = (
    BASE_DIR
    / "app"
    / "ml"
    / "models"
    / "transaction_categorizer.joblib"
)

REPORT_DIR = BASE_DIR / "docs"

REPORT_PATH = (
    REPORT_DIR / "independent_category_evaluation.json"
)


def load_independent_data() -> tuple[list[str], list[str]]:
    """Load and validate the independent test messages."""

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, list) or not dataset:
        raise ValueError("The independent test dataset is empty or invalid.")

    texts = []
    labels = []

    for item in dataset:
        text = item.get("text", "").strip()
        category = item.get("category", "").strip()

        if not text or not category:
            raise ValueError(
                "Every test example must have text and a category."
            )

        texts.append(text)
        labels.append(category)

    return texts, labels


def evaluate_independent_model() -> None:
    """Evaluate the saved model without retraining it."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Trained model not found. Run python -m app.ml.train first."
        )

    model = joblib.load(MODEL_PATH)

    texts, actual_labels = load_independent_data()

    # Predict categories for the independent messages.
    predictions = model.predict(texts)

    # Use the same category order as the trained model.
    categories = list(model.classes_)

    # Generate classification metrics.
    report = classification_report(
        actual_labels,
        predictions,
        labels=categories,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        actual_labels,
        predictions,
        labels=categories,
    )

    accuracy = accuracy_score(actual_labels, predictions)

    # Identify incorrectly classified messages.
    misclassified = []

    probabilities = model.predict_proba(texts)

    for text, actual, predicted, scores in zip(
        texts,
        actual_labels,
        predictions,
        probabilities,
        strict=True,
    ):
        if actual != predicted:
            predicted_index = list(model.classes_).index(predicted)

            misclassified.append(
                {
                    "text": text,
                    "actual_category": actual,
                    "predicted_category": str(predicted),
                    "confidence": float(scores[predicted_index]),
                }
            )

    # Prepare the evaluation results.
    results = {
        "test_examples": len(texts),
        "categories": categories,
        "accuracy": float(accuracy),
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
        "misclassified_examples": misclassified,
    }

    # Save the independent evaluation report.
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)

    # Display the evaluation results.
    print("\nINDEPENDENT MODEL EVALUATION")
    print("----------------------------")

    print(f"Test examples: {len(texts)}")
    print(f"Accuracy: {accuracy:.2%}")

    print("\nClassification Report:")
    print(
        classification_report(
            actual_labels,
            predictions,
            labels=categories,
            zero_division=0,
        )
    )

    print("Confusion Matrix:")
    print(matrix)

    print(f"\nMisclassified messages: {len(misclassified)}")

    if misclassified:
        print("\nMISCLASSIFIED EXAMPLES")
        print("----------------------")

        for index, item in enumerate(misclassified, start=1):
            print(f"\n{index}. Message: {item['text']}")
            print(f"   Actual: {item['actual_category']}")
            print(f"   Predicted: {item['predicted_category']}")
            print(f"   Confidence: {item['confidence']:.2%}")

    print(f"\nReport saved to: {REPORT_PATH}")


if __name__ == "__main__":
    evaluate_independent_model()
