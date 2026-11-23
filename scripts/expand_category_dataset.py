
"""Expand the MoneyLens UG synthetic category training dataset."""

import json
from itertools import product
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "category_training_data.json"
)

TARGET_PER_CATEGORY = 100

# Keep the categories consistent with the application.
CATEGORY_TEMPLATES = {
    "Transfers": [
        "Sent UGX {amount} to a mobile money contact.",
        "Received UGX {amount} from another mobile money user.",
        "Transferred UGX {amount} to a registered mobile wallet.",
        "Moved UGX {amount} from my bank account to mobile money.",
        "Received a bank transfer of UGX {amount}.",
        "Sent UGX {amount} to a friend's phone number.",
        "A mobile money transfer of UGX {amount} was completed.",
        "UGX {amount} was credited through a bank transfer.",
    ],
    "Cash": [
        "Withdrew UGX {amount} from a mobile money agent.",
        "Deposited UGX {amount} with a mobile money agent.",
        "Collected UGX {amount} in cash from an agent.",
        "Cash withdrawal of UGX {amount} completed successfully.",
        "Added UGX {amount} to my mobile money wallet at an agent.",
        "Received cash worth UGX {amount} from the agent.",
        "Agent processed a cash deposit of UGX {amount}.",
        "UGX {amount} was withdrawn from my wallet in cash.",
    ],
    "Airtime & Data": [
        "Purchased UGX {amount} airtime for my phone.",
        "Bought a mobile internet bundle worth UGX {amount}.",
        "Data subscription payment of UGX {amount} completed.",
        "Recharged my phone with UGX {amount} airtime.",
        "Purchased a daily data package for UGX {amount}.",
        "A mobile data bundle costing UGX {amount} was activated.",
        "Paid UGX {amount} for internet bundles.",
        "Airtime recharge of UGX {amount} was successful.",
    ],
    "Utilities": [
        "Paid UGX {amount} for UMEME electricity.",
        "Settled my NWSC water bill of UGX {amount}.",
        "Electricity token purchased for UGX {amount}.",
        "Paid the monthly water supply bill worth UGX {amount}.",
        "UMEME payment of UGX {amount} completed.",
        "Purchased an electricity unit token costing UGX {amount}.",
        "Paid my water utility account UGX {amount}.",
        "Water and electricity service payment of UGX {amount}.",
    ],
    "Entertainment": [
        "Paid UGX {amount} for my DSTV subscription.",
        "Renewed my television subscription for UGX {amount}.",
        "Purchased a monthly entertainment package worth UGX {amount}.",
        "DSTV account payment of UGX {amount} was successful.",
        "Paid for television channels costing UGX {amount}.",
        "Renewed my home TV package using UGX {amount}.",
        "Entertainment subscription payment of UGX {amount}.",
        "Paid UGX {amount} to restore my television service.",
    ],
    "Government": [
        "Paid UGX {amount} to URA for tax obligations.",
        "Completed a government tax payment of UGX {amount}.",
        "Settled my URA payment reference for UGX {amount}.",
        "Paid UGX {amount} for a government revenue assessment.",
        "Submitted a tax payment worth UGX {amount}.",
        "Government revenue payment of UGX {amount} completed.",
        "Paid the assessed tax amount of UGX {amount}.",
        "URA received a payment of UGX {amount}.",
    ],
    "Food & Groceries": [
        "Bought groceries at Carrefour for UGX {amount}.",
        "Paid for supermarket shopping worth UGX {amount}.",
        "Purchased food items costing UGX {amount}.",
        "Paid UGX {amount} for lunch at a restaurant.",
        "Bought household groceries for UGX {amount}.",
        "Paid for vegetables and other food supplies worth UGX {amount}.",
        "Carrefour supermarket purchase of UGX {amount}.",
        "Restaurant bill settled using UGX {amount}.",
    ],
    "Transport": [
        "Paid FARAS UGX {amount} for a ride.",
        "BOLT trip payment of UGX {amount} completed.",
        "Paid SafeBoda UGX {amount} for motorcycle transport.",
        "Purchased fuel worth UGX {amount} at Shell.",
        "Paid TotalEnergies UGX {amount} for fuel.",
        "Transport fare of UGX {amount} paid through mobile money.",
        "Used a ride service and paid UGX {amount}.",
        "Paid a driver UGX {amount} for transportation.",
    ],
    "Shopping": [
        "Purchased household items through Jumia for UGX {amount}.",
        "Paid an online retailer UGX {amount} for an order.",
        "Bought clothing worth UGX {amount} from a retail shop.",
        "Completed an online shopping order worth UGX {amount}.",
        "Paid UGX {amount} for electronics purchased from a store.",
        "Purchased accessories costing UGX {amount}.",
        "Paid a merchant for a retail purchase of UGX {amount}.",
        "Received confirmation for an online order payment of UGX {amount}.",
    ],
    "Other": [
        "Paid UGX {amount} to Kato General Services.",
        "A payment of UGX {amount} was made to a local service provider.",
        "Paid UGX {amount} for a miscellaneous service.",
        "A merchant received UGX {amount} for an unspecified service.",
        "Completed a payment of UGX {amount} to a local business.",
        "Paid a service provider UGX {amount} using mobile money.",
        "A transaction of UGX {amount} was completed with an unfamiliar merchant.",
        "Paid UGX {amount} for a service not listed in my usual expenses.",
    ],
}

# Different transaction amounts create additional examples.
AMOUNTS = [
    2000,
    3500,
    5000,
    7500,
    10000,
    12500,
    15000,
    20000,
    25000,
    35000,
]


def load_dataset() -> list[dict[str, str]]:
    """Load and validate the existing synthetic dataset."""

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError("The training dataset must be a JSON list.")

    for item in dataset:
        if not isinstance(item, dict):
            raise ValueError("Every training example must be an object.")

        if not isinstance(item.get("text"), str):
            raise ValueError("Every example must contain text.")

        if not isinstance(item.get("category"), str):
            raise ValueError("Every example must contain a category.")

        if not item["text"].strip() or not item["category"].strip():
            raise ValueError("Training examples cannot contain empty fields.")

    return dataset


def expand_dataset() -> None:
    """Expand the dataset to the target number per category."""

    dataset = load_dataset()

    # Track existing examples to prevent duplicates.
    existing_texts = {
        item["text"].strip().casefold()
        for item in dataset
    }

    # Count existing examples in each category.
    category_counts = {
        category: sum(
            item["category"] == category
            for item in dataset
        )
        for category in CATEGORY_TEMPLATES
    }

    print("CURRENT DATASET")
    print("----------------")

    for category, count in category_counts.items():
        print(f"{category}: {count}")

    # Generate additional examples only where needed.
    for category, templates in CATEGORY_TEMPLATES.items():
        missing = TARGET_PER_CATEGORY - category_counts[category]

        if missing <= 0:
            continue

        generated = []

        # Combine transaction descriptions with different amounts.
        for template, amount in product(templates, AMOUNTS):
            text = template.format(amount=f"{amount:,}")

            if text.casefold() in existing_texts:
                continue

            generated.append(
                {
                    "text": text,
                    "category": category,
                }
            )

            existing_texts.add(text.casefold())

            if len(generated) == missing:
                break

        if len(generated) < missing:
            raise ValueError(
                f"Not enough unique templates for {category}. "
                f"Need {missing}, generated {len(generated)}."
            )

        dataset.extend(generated)

        print(
            f"\n{category}: added {len(generated)} examples"
        )

    # Confirm every category has reached the target.
    final_counts = {
        category: sum(
            item["category"] == category
            for item in dataset
        )
        for category in CATEGORY_TEMPLATES
    }

    if any(
        count != TARGET_PER_CATEGORY
        for count in final_counts.values()
    ):
        raise ValueError(
            f"Dataset counts are incorrect: {final_counts}"
        )

    # Save the expanded dataset.
    with DATASET_PATH.open("w", encoding="utf-8") as file:
        json.dump(dataset, file, indent=4, ensure_ascii=False)

    print("\nEXPANSION COMPLETE")
    print("------------------")
    print(f"Total examples: {len(dataset)}")

    for category, count in final_counts.items():
        print(f"{category}: {count}")

    print(f"\nDataset saved to: {DATASET_PATH}")


if __name__ == "__main__":
    expand_dataset()
