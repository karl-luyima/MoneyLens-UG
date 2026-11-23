
"""API endpoints for uploading and retrieving mobile money data."""

import csv
import io
import math
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.upload import Upload
from app.models.user import User
from app.schemas.upload import (
    MessageUploadRequest,
    UploadListResponse,
    UploadResponse,
)
from app.services.upload_service import process_messages

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"],
)


# Maximum permitted upload size: 5 MB.
MAX_UPLOAD_SIZE = 5 * 1024 * 1024

# Recognised CSV column names.
MESSAGE_COLUMNS = {
    "message",
    "sms",
    "raw_message",
    "transaction_message",
}


@router.post(
    "/messages",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_messages(
    request: MessageUploadRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UploadResponse:
    """Upload pasted mobile money SMS messages."""

    # Ignore blank messages before processing.
    messages = [message.strip() for message in request.messages if message.strip()]

    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one non-empty message is required.",
        )

    upload = process_messages(
        db=db,
        user_id=current_user.id,
        messages=messages,
        source_type="text",
    )

    return UploadResponse.model_validate(upload)


@router.post(
    "/file",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File(...)],
) -> UploadResponse:
    """Upload and process a TXT or CSV mobile money statement."""

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    # Accept only TXT and CSV files.
    extension = Path(file.filename).suffix.lower()

    if extension not in {".txt", ".csv"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt and .csv files are supported.",
        )

    # Read at most 5 MB plus one byte to detect oversized files.
    content = await file.read(MAX_UPLOAD_SIZE + 1)

    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the maximum allowed size of 5 MB.",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    # Decode text files and CSV files.
    try:
        decoded_content = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file must use UTF-8 text encoding.",
        ) from None

    messages: list[str] = []

    if extension == ".txt":
        # Ignore blank lines in TXT files.
        messages = [
            line.strip() for line in decoded_content.splitlines() if line.strip()
        ]

    elif extension == ".csv":
        csv_reader = csv.reader(io.StringIO(decoded_content))
        rows = list(csv_reader)

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The CSV file contains no records.",
            )

        # Check whether the first row contains a recognised header.
        first_row = [cell.strip().lower() for cell in rows[0]]

        message_column = next(
            (
                index
                for index, column in enumerate(first_row)
                if column in MESSAGE_COLUMNS
            ),
            None,
        )

        if message_column is not None:
            rows = rows[1:]
        else:
            # If there is no recognised header, use the first column.
            message_column = 0

        for row in rows:
            if len(row) > message_column:
                message = row[message_column].strip()

                if message:
                    messages.append(message)

    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No mobile money messages were found in the file.",
        )

    # Process the extracted messages using the Phase 1 parser.
    upload = process_messages(
        db=db,
        user_id=current_user.id,
        messages=messages,
        source_type="file",
        filename=Path(file.filename).name,
    )

    return UploadResponse.model_validate(upload)


@router.get(
    "",
    response_model=UploadListResponse,
)
def get_upload_history(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> UploadListResponse:
    """Retrieve the authenticated user's upload history."""

    # Always restrict results to the authenticated user.
    base_query = select(Upload).where(Upload.user_id == current_user.id)

    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

    uploads = db.scalars(
        base_query.order_by(Upload.created_at.desc(), Upload.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return UploadListResponse(
        items=[UploadResponse.model_validate(upload) for upload in uploads],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )
