"""Pydantic schemas for transaction categories."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryResponse(BaseModel):
    """Category information returned by the API."""

    id: int
    user_id: int | None
    name: str
    description: str | None
    is_system: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)