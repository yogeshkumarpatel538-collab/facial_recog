from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.camera_repository import CameraRepository
from app.schemas.analytics import (
    CameraAnalyticsResponse,
    CountSummary,
    DailyCount,
    HourlyCount,
    MonthlyCount,
    PaginatedResponse,
)

logger = get_logger(__name__)


class AnalyticsService:
    def __init__(self, db: Session):
        self.repo = AnalyticsRepository(db)
        self.camera_repo = CameraRepository(db)

    def get_today(
        self,
        *,
        target_date: Optional[date] = None,
        camera_id: Optional[int] = None,
    ) -> CountSummary:
        summary_date = target_date or date.today()
        self._validate_camera(camera_id)

        totals = self.repo.get_today_totals(summary_date, camera_id=camera_id)
        logger.debug(
            "Today analytics date=%s camera_id=%s in=%s out=%s",
            summary_date,
            camera_id,
            totals.total_in,
            totals.total_out,
        )
        return CountSummary(
            date=summary_date,
            total_in=totals.total_in,
            total_out=totals.total_out,
        )

    def get_hourly(
        self,
        *,
        target_date: Optional[date] = None,
        camera_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 24,
    ) -> PaginatedResponse[HourlyCount]:
        summary_date = target_date or date.today()
        self._validate_camera(camera_id)
        self._validate_pagination(skip, limit, max_limit=24)

        rows, total = self.repo.get_hourly_counts(
            summary_date,
            camera_id=camera_id,
            skip=skip,
            limit=limit,
        )
        return PaginatedResponse[HourlyCount](
            items=[
                HourlyCount(hour=row.hour, total_in=row.total_in, total_out=row.total_out)
                for row in rows
            ],
            total=total,
            skip=skip,
            limit=limit,
        )

    def get_daily(
        self,
        *,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        camera_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 31,
    ) -> PaginatedResponse[DailyCount]:
        end = end_date or date.today()
        start = start_date or (end - timedelta(days=30))
        self._validate_date_range(start, end)
        self._validate_camera(camera_id)
        self._validate_pagination(skip, limit, max_limit=366)

        rows, total = self.repo.get_daily_counts(
            start,
            end,
            camera_id=camera_id,
            skip=skip,
            limit=limit,
        )
        return PaginatedResponse[DailyCount](
            items=[
                DailyCount(
                    date=row.summary_date,
                    total_in=row.total_in,
                    total_out=row.total_out,
                )
                for row in rows
            ],
            total=total,
            skip=skip,
            limit=limit,
        )

    def get_monthly(
        self,
        *,
        year: Optional[int] = None,
        camera_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 12,
    ) -> PaginatedResponse[MonthlyCount]:
        self._validate_camera(camera_id)
        self._validate_pagination(skip, limit, max_limit=120)

        rows, total = self.repo.get_monthly_counts(
            year=year,
            camera_id=camera_id,
            skip=skip,
            limit=limit,
        )
        return PaginatedResponse[MonthlyCount](
            items=[
                MonthlyCount(
                    year=row.year,
                    month=row.month,
                    total_in=row.total_in,
                    total_out=row.total_out,
                )
                for row in rows
            ],
            total=total,
            skip=skip,
            limit=limit,
        )

    def get_camera_analytics(
        self,
        camera_id: int,
        *,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 31,
    ) -> CameraAnalyticsResponse:
        camera = self.camera_repo.get_by_id(camera_id)
        if not camera:
            raise NotFoundError("Camera not found")

        end = end_date or date.today()
        start = start_date or (end - timedelta(days=30))
        self._validate_date_range(start, end)
        self._validate_pagination(skip, limit, max_limit=366)

        totals = self.repo.get_camera_period_totals(camera_id, start, end)
        daily = self.get_daily(
            start_date=start,
            end_date=end,
            camera_id=camera_id,
            skip=skip,
            limit=limit,
        )

        return CameraAnalyticsResponse(
            camera_id=camera.id,
            camera_name=camera.name,
            location=camera.location,
            start_date=start,
            end_date=end,
            total_in=totals.total_in,
            total_out=totals.total_out,
            daily=daily,
        )

    def _validate_camera(self, camera_id: Optional[int]) -> None:
        if camera_id is None:
            return
        if not self.camera_repo.get_by_id(camera_id):
            raise NotFoundError("Camera not found")

    @staticmethod
    def _validate_date_range(start: date, end: date) -> None:
        if start > end:
            raise ValidationError("start_date must be on or before end_date")

    @staticmethod
    def _validate_pagination(skip: int, limit: int, max_limit: int) -> None:
        if limit > max_limit:
            raise ValidationError(f"limit must not exceed {max_limit}")
