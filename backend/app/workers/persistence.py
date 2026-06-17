from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.count_event import Direction
from app.models.daily_summary import DailySummary
from app.realtime.publisher import RedisCountPublisher
from app.realtime.schemas import LiveCountUpdate
from app.repositories.count_event_repository import CountEventRepository
from app.repositories.daily_summary_repository import DailySummaryRepository
from app.workers.types import CrossingEvent

logger = get_logger(__name__)


class CountPersistenceService:
    """Persists crossing events, updates daily summaries, and publishes live updates."""

    def __init__(
        self,
        db: Session,
        publisher: Optional[RedisCountPublisher] = None,
    ):
        self.db = db
        self.event_repo = CountEventRepository(db)
        self.summary_repo = DailySummaryRepository(db)
        self._publisher = publisher

    @property
    def publisher(self) -> RedisCountPublisher:
        if self._publisher is None:
            self._publisher = RedisCountPublisher(enabled=settings.redis_enabled)
        return self._publisher

    def persist_crossing(
        self,
        camera_id: int,
        event: CrossingEvent,
    ) -> bool:
        direction = Direction(event.direction)
        track_id = str(event.track_id)

        if self.event_repo.get_by_track_and_direction(camera_id, track_id, direction):
            logger.debug(
                "DB duplicate skipped camera_id=%s track_id=%s direction=%s",
                camera_id,
                track_id,
                direction.value,
            )
            return False

        try:
            self.event_repo.create_event(
                camera_id=camera_id,
                track_id=track_id,
                direction=direction,
                timestamp=event.timestamp,
            )
            summary = self.summary_repo.increment(
                camera_id=camera_id,
                summary_date=event.timestamp.date(),
                direction=direction,
            )
            self._publish_live_count(summary)
            logger.info(
                "Persisted %s count camera_id=%s track_id=%s",
                direction.value,
                camera_id,
                track_id,
            )
            return True
        except Exception:
            self.db.rollback()
            logger.exception(
                "Failed to persist crossing camera_id=%s track_id=%s",
                camera_id,
                track_id,
            )
            raise

    def persist_batch(
        self,
        camera_id: int,
        events: list[CrossingEvent],
    ) -> int:
        saved = 0
        for event in events:
            if self.persist_crossing(camera_id, event):
                saved += 1
        return saved

    def _publish_live_count(self, summary: DailySummary) -> None:
        update = LiveCountUpdate(
            camera_id=summary.camera_id,
            total_in=summary.total_in,
            total_out=summary.total_out,
        )
        self.publisher.publish(update)
