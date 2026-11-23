
"""Predefined categories and default rules for transaction categorization."""

# These categories are shared by all MoneyLens UG users.
# Default keyword rules will be copied to individual users so they
# can customise their own rules without affecting other users.

SYSTEM_CATEGORIES: tuple[dict[str, str], ...] = (
    {
        "name": "Transfers",
        "description": "Money sent, received, or transferred between accounts.",
    },
    {
        "name": "Cash",
        "description": "Cash deposits and cash withdrawals.",
    },
    {
        "name": "Airtime & Data",
        "description": "Airtime purchases and mobile data payments.",
    },
    {
        "name": "Utilities",
        "description": "Electricity, water, and other utility payments.",
    },
    {
        "name": "Entertainment",
        "description": "Television subscriptions and entertainment services.",
    },
    {
        "name": "Government",
        "description": "Government payments, taxes, and statutory fees.",
    },
    {
        "name": "Food & Groceries",
        "description": "Food purchases, supermarkets, and groceries.",
    },
    {
        "name": "Transport",
        "description": "Transport fares, ride-hailing, and fuel expenses.",
    },
    {
        "name": "Shopping",
        "description": "General shopping and retail purchases.",
    },
    {
        "name": "Other",
        "description": "Transactions that do not fit another category.",
    },
)


# Deterministic mappings based on the transaction types produced
# by the Phase 1 mobile money parser.
TRANSACTION_TYPE_CATEGORY_MAP: dict[str, str] = {
    "send_money": "Transfers",
    "receive_money": "Transfers",
    "cash_withdrawal": "Cash",
    "cash_deposit": "Cash",
    "airtime": "Airtime & Data",
    "bill_umeme": "Utilities",
    "bill_nwsc": "Utilities",
    "bill_dstv": "Entertainment",
    "bill_ura": "Government",
    "bank_transfer": "Transfers",
}


# Default keyword rules copied to each user's account.
# Matching will initially be performed against the counterparty field.
# Users will be able to customise these rules later.
DEFAULT_CATEGORY_RULES: tuple[dict[str, str], ...] = (
    {
        "keyword": "BOLT",
        "category_name": "Transport",
    },
    {
        "keyword": "SAFEBODA",
        "category_name": "Transport",
    },
    {
        "keyword": "FARAS",
        "category_name": "Transport",
    },
    {
        "keyword": "SHELL",
        "category_name": "Transport",
    },
    {
        "keyword": "TOTALENERGIES",
        "category_name": "Transport",
    },
    {
        "keyword": "CARREFOUR",
        "category_name": "Food & Groceries",
    },
    {
        "keyword": "CAPITAL SHOPPERS",
        "category_name": "Food & Groceries",
    },
    {
        "keyword": "QUALITY SUPERMARKET",
        "category_name": "Food & Groceries",
    },
    {
        "keyword": "JUMIA",
        "category_name": "Shopping",
    },
)
