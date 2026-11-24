
"""API endpoints for financial insights."""

from typing import Annotated

from fastapi import APIRouter, Depends
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
) -> InsightsSummaryResponse:
    """Retrieve financial insights for the authenticated user."""

    return generate_insights_summary(
        db=db,
        user_id=current_user.id,
    )
