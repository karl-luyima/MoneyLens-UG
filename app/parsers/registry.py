# The registry holds all ten parser classes and tries them in sequence
"""Registry responsible for selecting transaction parsers."""

from app.parsers.base import BaseParser
from app.parsers.models import ParsedTransaction, UnparsedResult
from app.parsers.transaction_parsers import (
    AirtimeParser,
    BankTransferParser,
    CashDepositParser,
    CashWithdrawalParser,
    DstvBillParser,
    NwscBillParser,
    ReceiveMoneyParser,
    SendMoneyParser,
    UmemeBillParser,
    UraBillParser,
)


class ParserRegistry:
    """Select and execute the appropriate transaction parser."""

    def __init__(self) -> None:
        self.parsers: list[BaseParser] = [
            SendMoneyParser(),
            ReceiveMoneyParser(),
            CashWithdrawalParser(),
            CashDepositParser(),
            AirtimeParser(),
            UmemeBillParser(),
            NwscBillParser(),
            DstvBillParser(),
            UraBillParser(),
            BankTransferParser(),
        ]

    def parse(
        self,
        message: str,
    ) -> ParsedTransaction | UnparsedResult:
        """Parse a message or return a reason it was not recognised."""

        for parser in self.parsers:
            if parser.can_parse(message):
                return parser.parse(message)

        return UnparsedResult(
            raw_message=message,
            reason="No registered parser recognised this message.",
        )
