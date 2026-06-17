import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import AuthenticationError

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(*, user_id: int, email: str, role: str) -> str:
    expire = _utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": TOKEN_TYPE_ACCESS,
        "exp": expire,
        "iat": _utcnow(),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, user_id: int, email: str, role: str) -> tuple[str, str, datetime]:
    jti = str(uuid.uuid4())
    expire = _utcnow() + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": TOKEN_TYPE_REFRESH,
        "jti": jti,
        "exp": expire,
        "iat": _utcnow(),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expire


def decode_token(token: str, *, expected_type: Optional[str] = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired token") from exc

    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise AuthenticationError(f"Invalid token type: expected {expected_type}")

    if not payload.get("sub"):
        raise AuthenticationError("Token missing subject")

    return payload
