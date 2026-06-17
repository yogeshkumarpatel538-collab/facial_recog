from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.models.count_event import CountEvent, Direction
from app.models.daily_summary import DailySummary
from app.models.user import User, UserRole
from app.repositories.camera_repository import CameraRepository
from app.repositories.count_event_repository import CountEventRepository
from app.repositories.daily_summary_repository import DailySummaryRepository
from app.repositories.user_repository import UserRepository
from app.schemas import CountEventCreate, DailySummaryCreate, UserCreate
from app.services.camera_service import CameraService
from app.utils.security import hash_password

logger = get_logger(__name__)


class CountEventService:
    def __init__(self, db: Session):
        self.repo = CountEventRepository(db)
        self.camera_repo = CameraRepository(db)

    def record_event(self, payload: CountEventCreate) -> CountEvent:
        if not self.camera_repo.get_by_id(payload.camera_id):
            raise NotFoundError("Camera not found")

        event = CountEvent(
            camera_id=payload.camera_id,
            track_id=payload.track_id,
            direction=payload.direction,
            timestamp=payload.timestamp or datetime.now(timezone.utc),
        )
        logger.info(
            "Recording count event: camera=%s direction=%s track=%s",
            payload.camera_id,
            payload.direction.value,
            payload.track_id,
        )
        return self.repo.create(event)

    def list_events(self, camera_id: int, skip: int = 0, limit: int = 100) -> List[CountEvent]:
        return self.repo.get_by_camera(camera_id, skip=skip, limit=limit)


class DailySummaryService:
    def __init__(self, db: Session):
        self.repo = DailySummaryRepository(db)
        self.camera_repo = CameraRepository(db)

    def get_summary(self, camera_id: int, summary_date: date) -> DailySummary:
        summary = self.repo.get_by_camera_and_date(camera_id, summary_date)
        if not summary:
            raise NotFoundError("Daily summary not found")
        return summary

    def list_summaries(self, camera_id: int) -> List[DailySummary]:
        return self.repo.get_by_camera(camera_id)

    def create_or_update_summary(self, payload: DailySummaryCreate) -> DailySummary:
        if not self.camera_repo.get_by_id(payload.camera_id):
            raise NotFoundError("Camera not found")
        return self.repo.upsert(
            camera_id=payload.camera_id,
            summary_date=payload.date,
            total_in=payload.total_in,
            total_out=payload.total_out,
        )


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def create_user(self, payload: UserCreate) -> User:
        if self.repo.email_exists(payload.email):
            raise ConflictError("Email already registered")
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        logger.info("Creating user: %s", user.email)
        return self.repo.create(user)

    def get_user(self, user_id: int) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        return self.repo.get_by_email(email)

    def list_users(self, role: Optional[UserRole] = None) -> List[User]:
        if role:
            return self.repo.get_by_role(role)
        return self.repo.get_all()


__all__ = [
    "CameraService",
    "CountEventService",
    "DailySummaryService",
    "UserService",
]
