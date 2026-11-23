
"""Authentication API endpoints for MoneyLens UG."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new MoneyLens UG user."""

    # Check whether the email is already registered.
    existing_user = db.scalar(select(User).where(User.email == user_data.email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Hash the password before storing it.
    new_user = User(
        email=str(user_data.email),
        hashed_password=hash_password(user_data.password),
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from None

    return UserResponse.model_validate(new_user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user using JSON credentials."""

    user = db.scalar(select(User).where(User.email == str(credentials.email)))

    # Reject incorrect credentials.
    if user is None or not verify_password(
        credentials.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    # Generate access and refresh tokens.
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post(
    "/token",
    response_model=TokenResponse,
)
def oauth2_login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user using the OAuth2 password form."""

    # Swagger sends the email address in the username field.
    user = db.scalar(select(User).where(User.email == form_data.username))

    # Reject incorrect credentials.
    if user is None or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    # Generate access and refresh tokens.
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_access_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Generate new JWT tokens using a valid refresh token."""

    payload = decode_token(token_data.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user_id: Any = payload.get("sub")

    if not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from None

    user = db.scalar(select(User).where(User.id == user_id))

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is inactive.",
        )

    # Issue a new pair of tokens.
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
