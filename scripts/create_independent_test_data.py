
"""Create an independent synthetic Ugandan mobile money test dataset."""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "independent_test_data.json"
)

# All amounts, references and phone numbers are fictional.
AMOUNTS = [8500, 17500, 32000, 46500]
REFERENCES = ["MLX701", "MLX824", "MLX936", "MLX415"]

# Each category has five different message structures.
# Four variations of each structure produce 20 examples per category.
TEMPLATES = {
    "Transfers": [
        "Confirmed: UGX {amount} sent to 0700000001. Ref {ref}.",
        "Your wallet has been credited with UGX {amount}. Ref: {ref}.",
        "Transfer successful. You sent UGX {amount} to a mobile wallet. ID {ref}.",
        "UGX {amount} received from 0700000002 on 23/11/2026. Ref {ref}.",
        "Bank-to-wallet transfer of UGX {amount} completed. Reference {ref}.",
    ],
    "Cash": [
        "Agent transaction successful. You withdrew UGX {amount}. Ref {ref}.",
        "Cash-in completed: UGX {amount} added to your wallet. ID {ref}.",
        "You collected UGX {amount} from a cash agent. Ref {ref}.",
        "Your agent deposit of UGX {amount} was successful. Ref {ref}.",
        "Wallet cash withdrawal: UGX {amount}. Transaction {ref}.",
    ],
    "Airtime & Data": [
        "Airtime top-up of UGX {amount} completed. Ref {ref}.",
        "Your internet bundle purchase of UGX {amount} is active. ID {ref}.",
        "UGX {amount} deducted for a mobile data package. Ref {ref}.",
        "Recharge successful. Mobile credit worth UGX {amount}. {ref}.",
        "You have subscribed to a data package costing UGX {amount}. Ref {ref}.",
    ],
    "Utilities": [
        "UMEME Yaka payment received: UGX {amount}. Token purchase ref {ref}.",
        "NWSC account payment of UGX {amount} processed. Receipt {ref}.",
        "Electricity units payment successful. Amount UGX {amount}. Ref {ref}.",
        "Water bill settled using UGX {amount}. Confirmation {ref}.",
        "Utility payment accepted by UMEME. UGX {amount}. ID {ref}.",
    ],
    "Entertainment": [
        "Your DSTV account has been renewed. Payment UGX {amount}. Ref {ref}.",
        "Television subscription activated after payment of UGX {amount}. {ref}.",
        "UGX {amount} received for your TV package renewal. Receipt {ref}.",
        "Decoder subscription payment successful. UGX {amount}. Ref {ref}.",
        "Your entertainment package is active. Paid UGX {amount}. ID {ref}.",
    ],
    "Government": [
        "URA payment confirmed. Amount received UGX {amount}. PRN {ref}.",
        "Tax obligation payment of UGX {amount} successfully processed. Ref {ref}.",
        "Government revenue collection: UGX {amount} paid. Receipt {ref}.",
        "Your URA assessment has been settled with UGX {amount}. PRN {ref}.",
        "Tax payment accepted. Amount UGX {amount}. Payment reference {ref}.",
    ],
    "Food & Groceries": [
        "Payment to Carrefour Uganda: UGX {amount}. Merchant ref {ref}.",
        "POS purchase at a supermarket approved. UGX {amount}. Receipt {ref}.",
        "Your restaurant bill of UGX {amount} has been paid. Ref {ref}.",
        "Grocery purchase processed for UGX {amount}. Merchant ID {ref}.",
        "Payment for food supplies completed. UGX {amount}. Ref {ref}.",
    ],
    "Transport": [
        "FARAS trip completed. Fare charged: UGX {amount}. Trip {ref}.",
        "BOLT ride payment processed for UGX {amount}. Receipt {ref}.",
        "SafeBoda fare paid successfully. UGX {amount}. Trip ID {ref}.",
        "Fuel purchase at Shell approved. UGX {amount}. Ref {ref}.",
        "Your transport fare has been settled. UGX {amount}. Transaction {ref}.",
    ],
    "Shopping": [
        "Jumia order payment accepted. Total UGX {amount}. Order {ref}.",
        "Retail purchase approved at a clothing store. UGX {amount}. Ref {ref}.",
        "Payment for your electronics order: UGX {amount}. Receipt {ref}.",
        "Online merchant transaction successful. UGX {amount}. Order ID {ref}.",
        "Your household item purchase has been paid. UGX {amount}. Ref {ref}.",
    ],
    "Other": [
        "Payment to Kato General Services completed. UGX {amount}. Ref {ref}.",
        "Merchant collection successful. UGX {amount} paid to Mirembe Services. {ref}.",
        "Service charge payment processed for UGX {amount}. Receipt {ref}.",
        "A payment of UGX {amount} was made to a local business. ID {ref}.",
        (
            "Transaction completed with an independent service provider. "
            "UGX {amount}. {ref}."
        ),
    ],
}


def create_dataset() -> None:
    """Generate 200 independent synthetic test messages."""

    dataset = []

    for category, templates in TEMPLATES.items():
        for template in templates:
            for amount, reference in zip(
                AMOUNTS,
                REFERENCES,
                strict=True,
            ):
                message = template.format(
                    amount=f"{amount:,}",
                    ref=reference,
                )

                dataset.append(
                    {
                        "text": message,
                        "category": category,
                    }
                )

    if len(dataset) != 200:
        raise ValueError(
            f"Expected 200 messages, generated {len(dataset)}."
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(dataset, file, indent=4, ensure_ascii=False)

    print(f"Independent test messages: {len(dataset)}")
    print("\nCategory distribution:")

    for category in TEMPLATES:
        count = sum(
            item["category"] == category
            for item in dataset
        )
        print(f"{category}: {count}")

    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    create_dataset()
