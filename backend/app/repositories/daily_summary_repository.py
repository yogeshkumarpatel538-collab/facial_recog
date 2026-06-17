from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.count_event import Direction
from app.models.daily_summary import DailySummary
from app.repositories.base import BaseRepository


class DailySummaryRepository(BaseRepository[DailySummary]):
    def __init__(self, db: Session):
        super().__init__(DailySummary, db)

    def get_by_camera_and_date(
        self,
        camera_id: int,
        summary_date: date,
    ) -> Optional[DailySummary]:
        return (
            self.db.query(DailySummary)
            .filter(
                DailySummary.camera_id == camera_id,
                DailySummary.date == summary_date,
            )
            .first()
        )

    def get_by_camera(
        self,
        camera_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DailySummary]:
        return (
            self.db.query(DailySummary)
            .filter(DailySummary.camera_id == camera_id)
            .order_by(DailySummary.date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_date_range(
        self,
        camera_id: int,
        start_date: date,
        end_date: date,
    ) -> List[DailySummary]:
        return (
            self.db.query(DailySummary)
            .filter(
                DailySummary.camera_id == camera_id,
                DailySummary.date >= start_date,
                DailySummary.date <= end_date,
            )
            .order_by(DailySummary.date.asc())
            .all()
        )

    def upsert(
        self,
        camera_id: int,
        summary_date: date,
        total_in: int,
        total_out: int,
    ) -> DailySummary:
        summary = self.get_by_camera_and_date(camera_id, summary_date)
        if summary:
            summary.total_in = total_in
            summary.total_out = total_out
            return self.update(summary)

        summary = DailySummary(
            camera_id=camera_id,
            date=summary_date,
            total_in=total_in,
            total_out=total_out,
        )
        return self.create(summary)

    def increment(
        self,
        camera_id: int,
        summary_date: date,
        direction: Direction,
    ) -> DailySummary:
        summary = self.get_by_camera_and_date(camera_id, summary_date)
        if summary is None:
            summary = DailySummary(
                camera_id=camera_id,
                date=summary_date,
                total_in=0,
                total_out=0,
            )
            self.db.add(summary)

        if direction == Direction.IN:
            summary.total_in += 1
        else:
            summary.total_out += 1

        self.db.commit()
        self.db.refresh(summary)
        return summary
