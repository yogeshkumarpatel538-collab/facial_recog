from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.database.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.utils.jwt import TOKEN_TYPE_ACCESS, decode_token

bearer_scheme = HTTPBearer(
    scheme_name="JWT Bearer",
    description="Enter your JWT access token",
    auto_error=False,
)


async def get_current_user_from_token(token: str, db: Session) -> User:
    """Resolve user from a raw JWT access token (used by WebSocket auth)."""
    payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
    user_id = int(payload["sub"])

    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise AuthenticationError("User not found")
    return user


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a valid JWT access token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Not authenticated")

    return await get_current_user_from_token(credentials.credentials, db)


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require the current user to have the Admin role."""
    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError("Admin privileges required")
    return current_user


async def get_current_user_optional(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Session = Depends(get_db),
) -> User | None:
    """Return the current user if authenticated, otherwise None."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None

    try:
        return await get_current_user(credentials, db)
    except AuthenticationError:
        return None
