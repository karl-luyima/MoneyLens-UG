# Understanding the processing logic
# 1. Create an upload record
#   Each import gets its own database record, including the user and source.

# 2. Parse each message
#   The existing ParserRegistry tries the ten transaction-specific parsers.

# 3. Detect duplicates
#   The service checks transaction IDs against existing transactions
#   belonging to that user.

# 4. Save results
#   Parsed transactions go into transactions.
#   Unsuccessful messages go into unparsed_messages.

# 5. Update statistics
#   The upload records the parsed, duplicate and unparsed counts.

"""Service for processing uploaded mobile money messages."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.unparsed_message import UnparsedMessage
from app.models.upload import Upload
from app.parsers.models import ParsedTransaction
from app.parsers.registry import ParserRegistry

# Create one reusable parser registry.
parser_registry = ParserRegistry()


def process_messages(
    db: Session,
    user_id: int,
    messages: list[str],
    source_type: str,
    filename: str | None = None,
) -> Upload:
    """Parse messages, detect duplicates, and save processing results."""

    # Create an upload record to track this import.
    upload = Upload(
        user_id=user_id,
        source_type=source_type,
        filename=filename,
        total_messages=len(messages),
        parsed_count=0,
        duplicate_count=0,
        unparsed_count=0,
        status="processing",
    )

    db.add(upload)
    db.flush()

    # Track transaction IDs encountered during this upload.
    seen_transaction_ids: set[str] = set()

    # Process each message independently.
    for message in messages:
        # Ignore empty messages.
        message = message.strip()

        if not message:
            upload.unparsed_count += 1

            db.add(
                UnparsedMessage(
                    user_id=user_id,
                    upload_id=upload.id,
                    raw_message=message,
                    reason="Empty message provided.",
                )
            )

            continue

        # Send the message to the Phase 1 parser registry.
        result = parser_registry.parse(message)

        # Handle successfully parsed transactions.
        if isinstance(result, ParsedTransaction):
            transaction_id = result.transaction_id

            # Check whether this transaction has already appeared
            # in the current upload.
            if transaction_id in seen_transaction_ids:
                upload.duplicate_count += 1
                continue

            # Remember this transaction ID before checking the database.
            seen_transaction_ids.add(transaction_id)

            # Check whether this transaction already exists
            # for the current user.
            existing_transaction = db.scalar(
                select(Transaction).where(
                    Transaction.user_id == user_id,
                    Transaction.transaction_id == transaction_id,
                )
            )

            # Skip transactions that have already been imported.
            if existing_transaction:
                upload.duplicate_count += 1
                continue

            # Save the successfully parsed transaction.
            transaction = Transaction(
                user_id=user_id,
                upload_id=upload.id,
                transaction_id=transaction_id,
                provider=result.provider,
                transaction_type=result.type,
                amount=result.amount,
                fee=result.fee,
                balance_after=result.balance_after,
                counterparty=result.counterparty,
                timestamp=result.timestamp,
                raw_message=message,
            )

            db.add(transaction)
            upload.parsed_count += 1

        # Handle messages that could not be parsed.
        else:
            db.add(
                UnparsedMessage(
                    user_id=user_id,
                    upload_id=upload.id,
                    raw_message=result.raw_message,
                    reason=result.reason,
                )
            )

            upload.unparsed_count += 1

    # Mark processing as complete.
    upload.status = "completed"

    # Save the upload and all associated records.
    try:
        db.commit()
        db.refresh(upload)

    except Exception:
        db.rollback()
        raise

    return upload
