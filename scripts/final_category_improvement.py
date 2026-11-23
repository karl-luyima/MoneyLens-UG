
"""Add final targeted examples for Shopping and Food & Groceries."""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "category_training_data.json"
)

TARGET_CATEGORIES = {
    "Food & Groceries": [
        "Purchased fresh vegetables and fruit from a market for UGX {amount}.",
        "Paid for meat and other food supplies costing UGX {amount}.",
        "Bought groceries for the household at a supermarket. Total UGX {amount}.",
        "Paid for bread, milk and eggs at a food store. UGX {amount}.",
        "Restaurant meal order paid using UGX {amount}.",
        "Bought cooking oil, rice and flour worth UGX {amount}.",
        "Food shopping at a local grocery shop completed. UGX {amount}.",
        "Paid a bakery for bread and pastries costing UGX {amount}.",
        "Purchased fresh produce from a vegetable vendor. UGX {amount}.",
        "Supermarket food bill settled successfully. UGX {amount}.",
        "Paid for groceries including beans and maize flour. UGX {amount}.",
        "Restaurant dining payment processed for UGX {amount}.",
        "Bought dairy products and household food supplies. UGX {amount}.",
        "Paid for fish and other food items worth UGX {amount}.",
        "Food delivery order payment confirmed. UGX {amount}.",
    ],
    "Shopping": [
        "Purchased a new pair of shoes from a retail shop for UGX {amount}.",
        "Paid for clothing items bought from a fashion store. UGX {amount}.",
        "Bought a mobile phone accessory costing UGX {amount}.",
        "Purchased a household appliance from an electronics retailer. UGX {amount}.",
        "Paid for furniture purchased from a home goods store. UGX {amount}.",
        "Bought a handbag and other fashion accessories for UGX {amount}.",
        "Online order for electronic equipment paid. UGX {amount}.",
        "Purchased a shirt and trousers from a clothing shop. UGX {amount}.",
        "Paid a hardware store for building materials worth UGX {amount}.",
        "Bought kitchen utensils from a household goods retailer. UGX {amount}.",
        "Purchased a laptop accessory online for UGX {amount}.",
        "Retail store payment for a wristwatch. Amount UGX {amount}.",
        "Paid for cosmetics and personal care products. UGX {amount}.",
        "Purchased a school bag and stationery items worth UGX {amount}.",
        "Online retail purchase confirmed. Order total UGX {amount}.",
    ],
}

AMOUNTS = [
    "9,300",
    "14,600",
    "23,800",
    "41,200",
]


def improve_dataset() -> None:
    """Add 60 unique examples to each targeted category."""

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError("Training dataset must be a JSON list.")

    existing_texts = {
        item["text"].strip().casefold()
        for item in dataset
    }

    initial_counts = {
        category: sum(
            item["category"] == category
            for item in dataset
        )
        for category in TARGET_CATEGORIES
    }

    for category, templates in TARGET_CATEGORIES.items():
        added = 0

        for template in templates:
            for amount in AMOUNTS:
                message = template.format(amount=amount)

                if message.casefold() in existing_texts:
                    continue

                dataset.append(
                    {
                        "text": message,
                        "category": category,
                    }
                )

                existing_texts.add(message.casefold())
                added += 1

        if added != 60:
            raise ValueError(
                f"Expected 60 new examples for {category}, "
                f"but generated {added}."
            )

        print(f"{category}: added {added} examples")

    final_counts = {
        category: sum(
            item["category"] == category
            for item in dataset
        )
        for category in TARGET_CATEGORIES
    }

    for category in TARGET_CATEGORIES:
        if final_counts[category] != initial_counts[category] + 60:
            raise ValueError(
                f"Unexpected final count for {category}."
            )

    with DATASET_PATH.open("w", encoding="utf-8") as file:
        json.dump(dataset, file, indent=4, ensure_ascii=False)

    print("\nFINAL DATASET IMPROVEMENT COMPLETE")
    print(f"Total training examples: {len(dataset)}")

    for category, count in final_counts.items():
        print(f"{category}: {count}")


if __name__ == "__main__":
    improve_dataset()
