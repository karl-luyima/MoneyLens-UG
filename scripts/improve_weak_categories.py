
"""Add targeted synthetic examples to weaker MoneyLens categories."""

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
    "Transfers": [
        "You received a mobile money transfer from a registered sender. UGX {amount}.",
        "Incoming payment from another mobile wallet: UGX {amount}.",
        "A person sent you UGX {amount} through mobile money.",
        "Your account received a transfer of UGX {amount}.",
        "Mobile money received from a contact: UGX {amount}.",
        "A transfer into your wallet was successful. Amount UGX {amount}.",
        "You have received funds from another subscriber worth UGX {amount}.",
        "UGX {amount} has been sent to your wallet by another user.",
        "Your mobile wallet received an incoming transfer of UGX {amount}.",
        "Transfer received successfully from another phone number. UGX {amount}.",
        "An incoming bank transfer of UGX {amount} has been confirmed.",
        "Funds sent from a bank account to your account: UGX {amount}.",
        "Your account has received money from a bank transfer. UGX {amount}.",
        "A customer transferred UGX {amount} to your mobile wallet.",
        "Payment received from a mobile money subscriber. UGX {amount}.",
    ],
    "Utilities": [
        "Water charges paid to National Water and Sewerage Corporation: UGX {amount}.",
        "Your NWSC water account has been cleared with UGX {amount}.",
        "Water supply services payment confirmed. Amount UGX {amount}.",
        "Paid the outstanding water bill using UGX {amount}.",
        "NWSC has received your water bill payment of UGX {amount}.",
        "Monthly water charges settled successfully. UGX {amount}.",
        "UMEME prepaid electricity purchase completed for UGX {amount}.",
        "Electricity Yaka units purchased using UGX {amount}.",
        "Your electricity account payment was accepted. UGX {amount}.",
        "Power bill payment confirmed by UMEME. Amount UGX {amount}.",
        "Paid for domestic water services. UGX {amount}.",
        "Electricity service charges settled using UGX {amount}.",
        "Water account recharge completed successfully. UGX {amount}.",
        "Purchased prepaid power units worth UGX {amount}.",
        "Payment for household water supply processed. UGX {amount}.",
    ],
    "Food & Groceries": [
        "Carrefour supermarket purchase completed. Total UGX {amount}.",
        "Paid for groceries and household food at Carrefour. UGX {amount}.",
        "Supermarket bill settled at Carrefour Uganda for UGX {amount}.",
        "Purchased food products from a grocery retailer. UGX {amount}.",
        "Paid for fresh produce and groceries. Amount UGX {amount}.",
        "Food shopping transaction approved at a supermarket. UGX {amount}.",
        "Capital Shoppers grocery bill paid. UGX {amount}.",
        "Quality Supermarket food purchase confirmed. UGX {amount}.",
        "Bought cooking ingredients and food supplies for UGX {amount}.",
        "Payment for supermarket food items processed. UGX {amount}.",
        "Paid a restaurant for a meal order. Amount UGX {amount}.",
        "Restaurant dining bill completed using UGX {amount}.",
        "Purchased groceries including milk, bread and vegetables. UGX {amount}.",
        "Food items purchased from a local supermarket. Total UGX {amount}.",
        "Paid for fresh fruits and vegetables at a food store. UGX {amount}.",
    ],
}

AMOUNTS = [
    "6,200",
    "11,750",
    "18,400",
    "27,900",
]


def expand_weak_categories() -> None:
    """Add 60 unique examples to each targeted category."""

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError("Training dataset must be a JSON list.")

    existing_texts = {
        item["text"].strip().casefold()
        for item in dataset
    }

    for category, templates in TARGET_CATEGORIES.items():
        existing_count = sum(
            item["category"] == category
            for item in dataset
        )

        if existing_count != 100:
            raise ValueError(
                f"{category} currently has {existing_count} examples. "
                "Expected 100. Check the dataset before continuing."
            )

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
                f"Expected to add 60 examples to {category}, "
                f"but added {added}."
            )

        print(f"{category}: added {added} examples")

    # Verify the final category distribution.
    final_counts = {
        category: sum(
            item["category"] == category
            for item in dataset
        )
        for category in TARGET_CATEGORIES
    }

    expected_counts = {
        "Transfers": 160,
        "Utilities": 160,
        "Food & Groceries": 160,
    }

    if final_counts != expected_counts:
        raise ValueError(
            f"Unexpected category counts: {final_counts}"
        )

    with DATASET_PATH.open("w", encoding="utf-8") as file:
        json.dump(dataset, file, indent=4, ensure_ascii=False)

    print("\nDATASET IMPROVEMENT COMPLETE")
    print(f"Total training examples: {len(dataset)}")

    for category in TARGET_CATEGORIES:
        print(f"{category}: {final_counts[category]}")


if __name__ == "__main__":
    expand_weak_categories()
