"""Pydantic schemas for mobile money uploads."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageUploadRequest(BaseModel):
    """Request body for uploading pasted mobile money messages."""

    messages: list[str] = Field(min_length=1)


class UploadResponse(BaseModel):
    """Summary of a processed mobile money upload."""

    id: int
    source_type: str
    filename: str | None
    total_messages: int
    parsed_count: int
    duplicate_count: int
    unparsed_count: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadListResponse(BaseModel):
    """Paginated upload history response."""

    items: list[UploadResponse]
    total: int
    page: int
    page_size: int
    pages: int
