from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.logging import get_logger
from app.models.user import User, UserRole
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.utils.jwt import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.utils.security import hash_password, verify_password

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)

    def register(self, payload: UserRegisterRequest) -> User:
        if self.user_repo.email_exists(payload.email):
            raise ConflictError("Email already registered")

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=UserRole.VIEWER,
        )
        created = self.user_repo.create(user)
        logger.info("Registered new user: %s (role=%s)", created.email, created.role.value)
        return created

    def login(self, payload: UserLoginRequest) -> TokenResponse:
        user = self.user_repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        return self._issue_token_pair(user)

    def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token, expected_type=TOKEN_TYPE_REFRESH)
        jti = payload.get("jti")
        if not jti:
            raise AuthenticationError("Refresh token missing identifier")

        stored = self.refresh_token_repo.get_by_jti(jti)
        if not stored or not self.refresh_token_repo.is_valid(stored):
            raise AuthenticationError("Refresh token revoked or expired")

        user = self.user_repo.get_by_id(int(payload["sub"]))
        if not user:
            raise AuthenticationError("User no longer exists")

        self.refresh_token_repo.revoke(stored)
        return self._issue_token_pair(user)

    def logout(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token, expected_type=TOKEN_TYPE_REFRESH)
        jti = payload.get("jti")
        if not jti:
            return

        stored = self.refresh_token_repo.get_by_jti(jti)
        if stored and not stored.is_revoked:
            self.refresh_token_repo.revoke(stored)
            logger.info("Revoked refresh token for user_id=%s", stored.user_id)

    def _issue_token_pair(self, user: User) -> TokenResponse:
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )
        refresh_token, jti, expires_at = create_refresh_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )
        self.refresh_token_repo.create_token(user.id, jti, expires_at)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
