from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_role(self, role: UserRole, skip: int = 0, limit: int = 100):
        return (
            self.db.query(User)
            .filter(User.role == role)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None
