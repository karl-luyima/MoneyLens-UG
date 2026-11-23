
"""Service for initializing system categories and user category rules."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.system_categories import (
    DEFAULT_CATEGORY_RULES,
    SYSTEM_CATEGORIES,
)
from app.models.category import Category
from app.models.category_rule import CategoryRule


def seed_system_categories(db: Session) -> list[Category]:
    """Create missing shared system categories without duplicating existing ones."""

    # Retrieve the existing system categories.
    existing_categories = db.scalars(
        select(Category).where(
            Category.is_system.is_(True),
            Category.user_id.is_(None),
        )
    ).all()

    categories_by_name = {
        category.name: category for category in existing_categories
    }

    # Create only categories that do not already exist.
    for category_data in SYSTEM_CATEGORIES:
        category_name = category_data["name"]

        if category_name in categories_by_name:
            continue

        category = Category(
            user_id=None,
            name=category_name,
            description=category_data["description"],
            is_system=True,
        )

        db.add(category)
        categories_by_name[category_name] = category

    # Flush so newly created categories receive database IDs.
    db.flush()

    return list(categories_by_name.values())


def seed_default_category_rules(
    db: Session,
    user_id: int,
) -> list[CategoryRule]:
    """Create missing default keyword rules for an individual user."""

    # Retrieve all system categories.
    system_categories = db.scalars(
        select(Category).where(
            Category.is_system.is_(True),
            Category.user_id.is_(None),
        )
    ).all()

    categories_by_name = {
        category.name: category for category in system_categories
    }

    # Retrieve the user's existing keyword rules.
    existing_rules = db.scalars(
        select(CategoryRule).where(
            CategoryRule.user_id == user_id,
        )
    ).all()

    existing_keywords = {
        rule.keyword for rule in existing_rules
    }

    created_rules: list[CategoryRule] = []

    # Create only missing default rules.
    for rule_data in DEFAULT_CATEGORY_RULES:
        keyword = rule_data["keyword"]
        category_name = rule_data["category_name"]

        # Do not overwrite existing user rules.
        if keyword in existing_keywords:
            continue

        category = categories_by_name.get(category_name)

        # Skip rules whose categories have not been initialized.
        if category is None:
            continue

        rule = CategoryRule(
            user_id=user_id,
            category_id=category.id,
            keyword=keyword,
            match_field="counterparty",
            is_active=True,
        )

        db.add(rule)
        created_rules.append(rule)
        existing_keywords.add(keyword)

    db.flush()

    return created_rules


def initialize_user_categories(
    db: Session,
    user_id: int,
) -> tuple[list[Category], list[CategoryRule]]:
    """Initialize system categories and default rules for a user."""

    categories = seed_system_categories(db)

    rules = seed_default_category_rules(
        db=db,
        user_id=user_id,
    )

    return categories, rules
