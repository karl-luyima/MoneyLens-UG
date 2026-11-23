# We'll avoid repeating the same regex extraction logic in ten parser classes.
"""Shared extraction utilities for mobile money SMS messages."""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

DATE_PATTERNS = [
    "%d/%m/%Y %H:%M",
    "%Y-%m-%d %H:%M",
    "%d-%b-%Y %H:%M",
]


def extract_amount(message: str) -> Decimal | None:
    """Extract the first UGX amount from a message."""

    match = re.search(
        r"UGX\s*([\d,]+(?:\.\d{1,2})?)",
        message,
        re.IGNORECASE,
    )

    if not match:
        return None

    try:
        return Decimal(match.group(1).replace(",", ""))
    except InvalidOperation:
        return None


def extract_fee(message: str) -> Decimal | None:
    """Extract a transaction fee or charge, if present."""

    match = re.search(
        r"(?:Fee|Charge):\s*UGX\s*([\d,]+(?:\.\d{1,2})?)",
        message,
        re.IGNORECASE,
    )

    if not match:
        return None

    try:
        return Decimal(match.group(1).replace(",", ""))
    except InvalidOperation:
        return None


def extract_balance(message: str) -> Decimal | None:
    """Extract the remaining mobile money balance."""

    match = re.search(
        r"(?:New balance|Balance):\s*UGX\s*([\d,]+(?:\.\d{1,2})?)",
        message,
        re.IGNORECASE,
    )

    if not match:
        return None

    try:
        return Decimal(match.group(1).replace(",", ""))
    except InvalidOperation:
        return None


def extract_transaction_id(message: str) -> str | None:
    """Extract the transaction reference."""

    match = re.search(
        r"(?:Transaction ID|Ref):\s*([A-Z0-9]+)",
        message,
        re.IGNORECASE,
    )

    return match.group(1) if match else None


def extract_timestamp(message: str) -> datetime | None:
    """Extract and parse a supported date format."""

    match = re.search(
        r"Date:\s*(.+?)(?:\.|$)",
        message,
        re.IGNORECASE,
    )

    if not match:
        return None

    date_text = match.group(1).strip()

    for date_format in DATE_PATTERNS:
        try:
            return datetime.strptime(date_text, date_format)
        except ValueError:
            continue

    return None


def extract_counterparty(message: str) -> str | None:
    """Extract a counterparty name or phone number when available."""

    match = re.search(
        r"\b(?:to|from)\s+"
        r"(?:UGX\s*[\d,]+\s+)?"
        r"(\d{9,12}\s+\([^)]+\)|\d{9,12}|\([^)]+\))",
        message,
        re.IGNORECASE,
    )

    if match:
        return match.group(1).strip(" ()")

    match = re.search(
        r"\b(?:to|from)\s+([A-Z][A-Za-z ]+?)"
        r"(?:\s+successful|\s+Transaction ID|\s+Ref|[.]|$)",
        message,
        re.IGNORECASE,
    )

    return match.group(1).strip() if match else None
