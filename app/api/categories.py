
"""API endpoints for transaction categories and ML retraining."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.ml.retraining import retrain_user_model
from app.models.user import User

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.post("/retrain")
def retrain_category_model(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, int | str]:
    """Retrain the authenticated user's personalized categorization model."""

    try:
        result = retrain_user_model(
            db=db,
            user_id=current_user.id,
        )

        return {
            "message": "Personalized categorization model trained successfully.",
            "model_version": result["model_version"],
            "corrections_used": result["corrections_used"],
            "training_examples": result["training_examples"],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
