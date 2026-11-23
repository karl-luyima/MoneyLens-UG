
"""Service for automatically categorizing mobile money transactions."""

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.data.system_categories import TRANSACTION_TYPE_CATEGORY_MAP
from app.ml.predict import predict_category
from app.models.category import Category
from app.models.category_rule import CategoryRule
from app.models.transaction import Transaction

# Minimum confidence required before accepting an ML prediction.
ML_CONFIDENCE_THRESHOLD = 0.70


def categorize_transaction(
    db: Session,
    transaction: Transaction,
) -> int | None:
    """Determine the category ID for a transaction.

    Categorization priority:
    1. User-specific keyword rules.
    2. Transaction-type category mappings.
    3. ML prediction when confidence meets the threshold.

    Unmatched or low-confidence transactions remain uncategorized.
    """

    # First, check active keyword rules belonging to this transaction's user.
    # Only allow rules linked to system categories or that user's
    # own custom categories.
    if transaction.counterparty:
        rules = db.scalars(
            select(CategoryRule)
            .join(Category, CategoryRule.category_id == Category.id)
            .where(
                CategoryRule.user_id == transaction.user_id,
                CategoryRule.is_active.is_(True),
                CategoryRule.match_field == "counterparty",
                or_(
                    and_(
                        Category.is_system.is_(True),
                        Category.user_id.is_(None),
                    ),
                    Category.user_id == transaction.user_id,
                ),
            )
            .order_by(
                func.length(CategoryRule.keyword).desc(),
                CategoryRule.id.asc(),
            )
        ).all()

        # Prefer the longest matching keyword.
        counterparty = transaction.counterparty.casefold()

        for rule in rules:
            if rule.keyword.casefold() in counterparty:
                return rule.category_id

    # If no keyword rule matches, use the transaction-type mapping.
    category_name = TRANSACTION_TYPE_CATEGORY_MAP.get(
        transaction.transaction_type
    )

    if category_name:
        category = db.scalar(
            select(Category).where(
                Category.name == category_name,
                Category.is_system.is_(True),
                Category.user_id.is_(None),
            )
        )

        if category is not None:
            return category.id

    # If no deterministic category is found, try ML categorization.
    # Use the transaction description and counterparty as prediction text.
    prediction_text = " ".join(
        value
        for value in (
            transaction.raw_message,
            transaction.counterparty,
        )
        if value
    )

    try:
        prediction = predict_category(
            prediction_text,
            user_id=transaction.user_id,
        )
    except (FileNotFoundError, ValueError):
        # Keep the transaction uncategorized if the model is unavailable
        # or the prediction input is invalid.
        return None

    predicted_category = prediction["category"]
    confidence = prediction["confidence"]

    # Validate prediction values before using them.
    if not isinstance(predicted_category, str):
        return None

    if not isinstance(confidence, (int, float)):
        return None

    # Reject predictions below the minimum confidence threshold.
    if confidence < ML_CONFIDENCE_THRESHOLD:
        return None

    # Only accept predictions matching an existing system category.
    category = db.scalar(
        select(Category).where(
            Category.name == predicted_category,
            Category.is_system.is_(True),
            Category.user_id.is_(None),
        )
    )

    if category is not None:
        return category.id

    return None
