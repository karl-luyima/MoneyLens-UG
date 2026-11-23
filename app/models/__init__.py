"""Import all database models for SQLAlchemy metadata discovery."""

from app.models.category import Category
from app.models.category_rule import CategoryRule
from app.models.transaction import Transaction
from app.models.unparsed_message import UnparsedMessage
from app.models.upload import Upload
from app.models.user import User

__all__ = [
    "User",
    "Transaction",
    "Category",
    "CategoryRule",
    "Upload",
    "UnparsedMessage",
]
