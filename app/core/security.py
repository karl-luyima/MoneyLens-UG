#This file will handle three important authentication operations:
#1. Hashing passwords before storing them in PostgreSQL.
#2. Verifying passwords during login.
#3. Generating JWT access and refresh tokens.


"""Security utilities for password hashing and JWT authentication."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings


# Configure Argon2 password hashing.
password_hash = PasswordHash.recommended()


# Hash a user's password before saving it to the database.
def hash_password(password: str) -> str:
    """Generate a secure password hash."""
    return password_hash.hash(password)


# Verify a submitted password against its stored hash.
def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Check whether a password matches its stored hash."""
    return password_hash.verify(plain_password, hashed_password)


# Generate JWT access and refresh tokens.
def create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
) -> str:
    """Create a signed JWT token."""
    expire = datetime.now(timezone.utc) + expires_delta

    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": token_type,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm="HS256",
    )


def create_access_token(subject: str) -> str:
    """Create a short-lived access token."""
    return create_token(
        subject=subject,
        expires_delta=timedelta(
            minutes=settings.access_token_expire_minutes
        ),
        token_type="access",
    )


def create_refresh_token(subject: str) -> str:
    """Create a longer-lived refresh token."""
    return create_token(
        subject=subject,
        expires_delta=timedelta(
            days=settings.refresh_token_expire_days
        ),
        token_type="refresh",
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT token."""
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
        )
    except JWTError:
        return None
    