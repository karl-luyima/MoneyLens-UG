
"""Pydantic schemas for user authentication."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """Data required when registering a new user."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Credentials required when logging in."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):  #returns safe user information
    """Public user information returned by the API."""

    id: int
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel): #returns access and refresh tokens
    """JWT tokens returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel): #accepts a refresh token 
    """Refresh token submitted to obtain a new access token."""

    refresh_token: str
