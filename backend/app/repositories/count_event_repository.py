from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.count_event import CountEvent, Direction
from app.repositories.base import BaseRepository


class CountEventRepository(BaseRepository[CountEvent]):
    def __init__(self, db: Session):
        super().__init__(CountEvent, db)

    def get_by_camera(
        self,
        camera_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CountEvent]:
        return (
            self.db.query(CountEvent)
            .filter(CountEvent.camera_id == camera_id)
            .order_by(CountEvent.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_date_range(
        self,
        camera_id: int,
        start: datetime,
        end: datetime,
    ) -> List[CountEvent]:
        return (
            self.db.query(CountEvent)
            .filter(
                CountEvent.camera_id == camera_id,
                CountEvent.timestamp >= start,
                CountEvent.timestamp <= end,
            )
            .order_by(CountEvent.timestamp.asc())
            .all()
        )

    def get_by_track_id(
        self,
        camera_id: int,
        track_id: str,
    ) -> Optional[CountEvent]:
        return (
            self.db.query(CountEvent)
            .filter(
                CountEvent.camera_id == camera_id,
                CountEvent.track_id == track_id,
            )
            .first()
        )

    def get_by_track_and_direction(
        self,
        camera_id: int,
        track_id: str,
        direction: Direction,
    ) -> Optional[CountEvent]:
        return (
            self.db.query(CountEvent)
            .filter(
                CountEvent.camera_id == camera_id,
                CountEvent.track_id == track_id,
                CountEvent.direction == direction,
            )
            .first()
        )

    def create_event(
        self,
        camera_id: int,
        track_id: str,
        direction: Direction,
        timestamp: datetime | None = None,
    ) -> CountEvent:
        event = CountEvent(
            camera_id=camera_id,
            track_id=track_id,
            direction=direction,
            timestamp=timestamp or datetime.now(timezone.utc),
        )
        return self.create(event)
