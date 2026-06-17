from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: Session):
        super().__init__(RefreshToken, db)

    def get_by_jti(self, jti: str) -> Optional[RefreshToken]:
        return self.db.query(RefreshToken).filter(RefreshToken.jti == jti).first()

    def create_token(self, user_id: int, jti: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at)
        return self.create(token)

    def revoke(self, token: RefreshToken) -> RefreshToken:
        token.revoked_at = datetime.now(timezone.utc)
        return self.update(token)

    def revoke_all_for_user(self, user_id: int) -> int:
        now = datetime.now(timezone.utc)
        count = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .update({"revoked_at": now}, synchronize_session=False)
        )
        self.db.commit()
        return count

    def is_valid(self, token: RefreshToken) -> bool:
        if token.is_revoked:
            return False
        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at > datetime.now(timezone.utc)
