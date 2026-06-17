from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole
from app.utils.validators import validate_password_strength


class UserRegisterRequest(BaseModel):
    """Register a new viewer account."""

    email: EmailStr = Field(..., description="Unique email address", examples=["user@example.com"])
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, must include upper, lower, and digit)",
        examples=["SecurePass1"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        return validate_password_strength(value)


class UserLoginRequest(BaseModel):
    """Authenticate with email and password."""

    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=1, max_length=128, examples=["SecurePass1"])


class TokenRefreshRequest(BaseModel):
    """Exchange a refresh token for a new token pair."""

    refresh_token: str = Field(..., min_length=1, description="Valid JWT refresh token")


class TokenResponse(BaseModel):
    """JWT token pair returned on login or refresh."""

    access_token: str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type for Authorization header")


class UserProfileResponse(BaseModel):
    """Authenticated user profile."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: UserRole
    created_at: datetime


class MessageResponse(BaseModel):
    message: str
