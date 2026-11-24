
"""API endpoints for financial insights."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.insights import InsightsSummaryResponse
from app.services.insights_service import generate_insights_summary

router = APIRouter(
    prefix="/insights",
    tags=["Insights"],
)


@router.get(
    "/summary",
    response_model=InsightsSummaryResponse,
)
def get_insights_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> InsightsSummaryResponse:
    """Retrieve financial insights for the authenticated user."""

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date cannot be later than end_date.",
        )

    return generate_insights_summary(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
