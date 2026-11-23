"""
Generate synthetic MTN MoMo and Airtel Money SMS messages.

All names, phone numbers and transaction IDs are fictional.
The dataset is intended for parser development and testing.
"""

import json
from pathlib import Path
from random import Random

random = Random(42)

OUTPUT_DIR = Path("data/synthetic")
OUTPUT_FILE = OUTPUT_DIR / "messages.json"

PROVIDERS = ["MTN", "AIRTEL"]

TRANSACTION_TYPES = {
    "send_money": "sent",
    "receive_money": "received",
    "cash_withdrawal": "withdrawn",
    "cash_deposit": "deposited",
    "airtime": "airtime",
    "bill_umeme": "UMEME",
    "bill_nwsc": "NWSC",
    "bill_dstv": "DSTV",
    "bill_ura": "URA",
    "bank_transfer": "bank",
}

NAMES = [
    "John Doe",
    "Jane Smith",
    "Peter Brown",
    "Mary Jones",
    "David Wilson",
]

PHONE_NUMBERS = [
    "0772000111",
    "0772000222",
    "0703000111",
    "0703000222",
]

DATES = [
    "23/11/2026 09:30",
    "2026-11-23 10:15",
    "23-Nov-2026 14:20",
    "24/11/2026 16:45",
    "2026-11-25 08:10",
]


def format_amount(amount: int, variation: int) -> str:
    """Return an amount with or without thousands separators."""
    if variation == 1:
        return f"{amount:,}"
    return str(amount)


def generate_message(
    provider: str,
    transaction_type: str,
    variation: int,
    index: int,
) -> dict:
    """Generate one synthetic mobile money SMS record."""

    amount = random.choice([5000, 10000, 20000, 30000, 50000, 80000, 100000])

    fee = random.choice([200, 500, 700, 1000])
    balance = random.randint(50000, 500000)

    name = random.choice(NAMES)
    phone = random.choice(PHONE_NUMBERS)
    date = DATES[variation]
    transaction_id = f"{provider}{index:06d}"

    amount_text = format_amount(amount, variation)
    fee_text = format_amount(fee, variation)

    transaction_label = TRANSACTION_TYPES[transaction_type]

    if transaction_type == "send_money":
        description = f"You have sent UGX {amount_text} to {phone} ({name})."

    elif transaction_type == "receive_money":
        description = f"You have received UGX {amount_text} from {phone} ({name})."

    elif transaction_type == "cash_withdrawal":
        description = f"You have withdrawn UGX {amount_text}."

    elif transaction_type == "cash_deposit":
        description = f"You have deposited UGX {amount_text}."

    elif transaction_type == "airtime":
        description = f"Airtime purchase of UGX {amount_text} successful."

    elif transaction_type.startswith("bill_"):
        description = f"Payment of UGX {amount_text} to {transaction_label} successful."

    elif transaction_type == "bank_transfer":
        description = f"Bank transfer of UGX {amount_text} to {name} successful."

    if provider == "MTN":
        message = (
            f"{description} Transaction ID: {transaction_id}. "
            f"Fee: UGX {fee_text}. "
            f"New balance: UGX {balance:,}. Date: {date}."
        )
    else:
        message = (
            f"Airtel Money: {description} "
            f"Ref: {transaction_id}. "
            f"Charge: UGX {fee_text}. "
            f"Balance: UGX {balance:,}. Date: {date}."
        )

    # Variation 2: Missing transaction fee.
    if variation == 2:
        message = message.replace(f"Fee: UGX {fee_text}. ", "")
        message = message.replace(f"Charge: UGX {fee_text}. ", "")

    # Variation 3: Extra whitespace.
    if variation == 3:
        message = message.replace(" ", "  ", 2)

    # Variation 4: Truncated message.
    if variation == 4:
        message = message[: len(message) // 2]

    return {
        "message_id": f"MSG{index:04d}",
        "provider": provider,
        "expected_type": transaction_type,
        "expected_status": ("unparsed" if variation == 4 else "parsed"),
        "raw_message": message,
    }


def generate_dataset() -> list[dict]:
    """Generate 100 synthetic messages."""

    messages = []
    index = 1

    for provider in PROVIDERS:
        for transaction_type in TRANSACTION_TYPES:
            for variation in range(5):
                message = generate_message(
                    provider,
                    transaction_type,
                    variation,
                    index,
                )

                messages.append(message)
                index += 1

    return messages


def main() -> None:
    """Generate and save the synthetic dataset."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    messages = generate_dataset()

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(messages, file, indent=4, ensure_ascii=False)

    print("Synthetic dataset generated successfully!")
    print(f"Total messages: {len(messages)}")
    print(f"Providers: {len(PROVIDERS)}")
    print(f"Transaction scenarios: {len(TRANSACTION_TYPES)}")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
