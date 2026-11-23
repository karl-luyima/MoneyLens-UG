# Every transaction parser will follow the same interface.
"""Common interface for all mobile money parsers."""

from abc import ABC, abstractmethod

from app.parsers.models import ParsedTransaction, UnparsedResult


class BaseParser(ABC):
    """Abstract base class for transaction-specific parsers."""

    transaction_type: str

    @abstractmethod
    def can_parse(self, message: str) -> bool:
        """Return True if this parser recognises the message."""
        raise NotImplementedError

    @abstractmethod
    def parse(
        self,
        message: str,
    ) -> ParsedTransaction | UnparsedResult:
        """Convert a raw SMS into a structured result."""
        raise NotImplementedError
