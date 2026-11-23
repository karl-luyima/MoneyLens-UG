# This is where we define the ten transaction-specific parser classes.

# We use a reusable RegexTransactionParser instead of duplicating
# extraction logic across all ten transaction-specific parser classes.

"""Regex-based parsers for individual transaction types."""

import re

from pydantic import ValidationError

from app.parsers.base import BaseParser
from app.parsers.models import (
    ParsedTransaction,
    Provider,
    TransactionType,
    UnparsedResult,
)
from app.parsers.utils import (
    extract_amount,
    extract_balance,
    extract_counterparty,
    extract_fee,
    extract_timestamp,
    extract_transaction_id,
)


class RegexTransactionParser(BaseParser):
    """Shared implementation for regex-based transaction parsers."""

    transaction_type: TransactionType
    pattern: str

    def can_parse(self, message: str) -> bool:
        """Check whether the message matches this transaction type."""

        return bool(re.search(self.pattern, message, re.IGNORECASE))

    def parse(
        self,
        message: str,
    ) -> ParsedTransaction | UnparsedResult:
        """Extract transaction fields and validate the result."""

        provider: Provider = (
            "AIRTEL" if re.search(r"Airtel Money:", message, re.IGNORECASE) else "MTN"
        )

        amount = extract_amount(message)
        transaction_id = extract_transaction_id(message)
        timestamp = extract_timestamp(message)

        if amount is None:
            return UnparsedResult(
                raw_message=message,
                provider=provider,
                reason="Transaction amount could not be extracted.",
            )

        if transaction_id is None:
            return UnparsedResult(
                raw_message=message,
                provider=provider,
                reason="Transaction ID could not be extracted.",
            )

        if timestamp is None:
            return UnparsedResult(
                raw_message=message,
                provider=provider,
                reason="Transaction timestamp could not be extracted.",
            )

        try:
            return ParsedTransaction(
                type=self.transaction_type,
                amount=amount,
                fee=extract_fee(message),
                counterparty=extract_counterparty(message),
                balance_after=extract_balance(message),
                transaction_id=transaction_id,
                timestamp=timestamp,
                provider=provider,
            )
        except ValidationError as error:
            return UnparsedResult(
                raw_message=message,
                provider=provider,
                reason=f"Transaction validation failed: {error}",
            )


class SendMoneyParser(RegexTransactionParser):
    """Parser for outgoing person-to-person transfers."""

    transaction_type: TransactionType = "send_money"
    pattern = r"\bYou have sent UGX\b"


class ReceiveMoneyParser(RegexTransactionParser):
    """Parser for incoming person-to-person transfers."""

    transaction_type: TransactionType = "receive_money"
    pattern = r"\bYou have received UGX\b"


class CashWithdrawalParser(RegexTransactionParser):
    """Parser for cash withdrawals."""

    transaction_type: TransactionType = "cash_withdrawal"
    pattern = r"\bYou have withdrawn UGX\b"


class CashDepositParser(RegexTransactionParser):
    """Parser for cash deposits."""

    transaction_type: TransactionType = "cash_deposit"
    pattern = r"\bYou have deposited UGX\b"


class AirtimeParser(RegexTransactionParser):
    """Parser for airtime purchases."""

    transaction_type: TransactionType = "airtime"
    pattern = r"\bAirtime purchase of UGX\b"


class UmemeBillParser(RegexTransactionParser):
    """Parser for UMEME bill payments."""

    transaction_type: TransactionType = "bill_umeme"
    pattern = r"\bPayment of UGX[\d,]+ to UMEME\b"


class NwscBillParser(RegexTransactionParser):
    """Parser for NWSC bill payments."""

    transaction_type: TransactionType = "bill_nwsc"
    pattern = r"\bPayment of UGX[\d,]+ to NWSC\b"


class DstvBillParser(RegexTransactionParser):
    """Parser for DSTV bill payments."""

    transaction_type: TransactionType = "bill_dstv"
    pattern = r"\bPayment of UGX[\d,]+ to DSTV\b"


class UraBillParser(RegexTransactionParser):
    """Parser for URA bill payments."""

    transaction_type: TransactionType = "bill_ura"
    pattern = r"\bPayment of UGX[\d,]+ to URA\b"


class BankTransferParser(RegexTransactionParser):
    """Parser for bank transfers."""

    transaction_type: TransactionType = "bank_transfer"
    pattern = r"\bBank transfer of UGX\b"
