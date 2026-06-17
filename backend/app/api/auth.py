from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    MessageResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new viewer account",
    description=(
        "Create a new user account with the **Viewer** role. "
        "Password must be at least 8 characters and include uppercase, lowercase, and a digit."
    ),
    responses={
        201: {"description": "User registered successfully"},
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> User:
    return AuthService(db).register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain JWT tokens",
    description=(
        "Authenticate with email and password. Returns a short-lived **access token** "
        "and a long-lived **refresh token**."
    ),
    responses={
        200: {"description": "Authentication successful"},
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"},
    },
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return AuthService(db).login(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description=(
        "Exchange a valid refresh token for a new access/refresh token pair. "
        "The old refresh token is revoked (rotation)."
    ),
    responses={
        200: {"description": "Tokens refreshed successfully"},
        401: {"description": "Invalid or expired refresh token"},
        422: {"description": "Validation error"},
    },
)
def refresh_tokens(
    payload: TokenRefreshRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return AuthService(db).refresh_tokens(payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and revoke refresh token",
    description="Revoke the provided refresh token so it can no longer be used.",
    responses={
        200: {"description": "Logged out successfully"},
        401: {"description": "Invalid refresh token"},
    },
)
def logout(
    payload: TokenRefreshRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    AuthService(db).logout(payload.refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Return the profile of the currently authenticated user.",
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Not authenticated"},
    },
)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user
