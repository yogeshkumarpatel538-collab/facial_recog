from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Optional

from sqlalchemy import case, extract, func
from sqlalchemy.orm import Session

from app.models.count_event import CountEvent, Direction
from app.models.daily_summary import DailySummary


@dataclass(frozen=True)
class CountTotals:
    total_in: int
    total_out: int


@dataclass(frozen=True)
class HourlyRow:
    hour: int
    total_in: int
    total_out: int


@dataclass(frozen=True)
class DailyRow:
    summary_date: date
    total_in: int
    total_out: int


@dataclass(frozen=True)
class MonthlyRow:
    year: int
    month: int
    total_in: int
    total_out: int


class AnalyticsRepository:
    """Optimized aggregation queries for analytics endpoints."""

    def __init__(self, db: Session):
        self.db = db

    def get_today_totals(
        self,
        summary_date: date,
        camera_id: Optional[int] = None,
    ) -> CountTotals:
        start = datetime.combine(summary_date, time.min, tzinfo=timezone.utc)
        end = datetime.combine(summary_date, time.max, tzinfo=timezone.utc)

        query = self.db.query(
            func.coalesce(
                func.sum(case((CountEvent.direction == Direction.IN, 1), else_=0)),
                0,
            ).label("total_in"),
            func.coalesce(
                func.sum(case((CountEvent.direction == Direction.OUT, 1), else_=0)),
                0,
            ).label("total_out"),
        ).filter(
            CountEvent.timestamp >= start,
            CountEvent.timestamp <= end,
        )

        if camera_id is not None:
            query = query.filter(CountEvent.camera_id == camera_id)

        row = query.one()
        return CountTotals(total_in=int(row.total_in), total_out=int(row.total_out))

    def get_hourly_counts(
        self,
        summary_date: date,
        camera_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 24,
    ) -> tuple[list[HourlyRow], int]:
        start = datetime.combine(summary_date, time.min, tzinfo=timezone.utc)
        end = datetime.combine(summary_date, time.max, tzinfo=timezone.utc)

        hour_expr = extract("hour", CountEvent.timestamp).label("hour")

        base_query = (
            self.db.query(
                hour_expr,
                func.coalesce(
                    func.sum(case((CountEvent.direction == Direction.IN, 1), else_=0)),
                    0,
                ).label("total_in"),
                func.coalesce(
                    func.sum(case((CountEvent.direction == Direction.OUT, 1), else_=0)),
                    0,
                ).label("total_out"),
            )
            .filter(
                CountEvent.timestamp >= start,
                CountEvent.timestamp <= end,
            )
            .group_by(hour_expr)
            .order_by(hour_expr)
        )

        if camera_id is not None:
            base_query = base_query.filter(CountEvent.camera_id == camera_id)

        total = base_query.count()
        rows = base_query.offset(skip).limit(limit).all()

        items = [
            HourlyRow(
                hour=int(row.hour),
                total_in=int(row.total_in),
                total_out=int(row.total_out),
            )
            for row in rows
        ]
        return items, total

    def get_daily_counts(
        self,
        start_date: date,
        end_date: date,
        camera_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 31,
    ) -> tuple[list[DailyRow], int]:
        query = (
            self.db.query(
                DailySummary.date.label("summary_date"),
                func.coalesce(func.sum(DailySummary.total_in), 0).label("total_in"),
                func.coalesce(func.sum(DailySummary.total_out), 0).label("total_out"),
            )
            .filter(
                DailySummary.date >= start_date,
                DailySummary.date <= end_date,
            )
            .group_by(DailySummary.date)
            .order_by(DailySummary.date.desc())
        )

        if camera_id is not None:
            query = query.filter(DailySummary.camera_id == camera_id)

        total = query.count()
        rows = query.offset(skip).limit(limit).all()

        items = [
            DailyRow(
                summary_date=row.summary_date,
                total_in=int(row.total_in),
                total_out=int(row.total_out),
            )
            for row in rows
        ]
        return items, total

    def get_monthly_counts(
        self,
        year: Optional[int] = None,
        camera_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 12,
    ) -> tuple[list[MonthlyRow], int]:
        year_expr = extract("year", DailySummary.date).label("year")
        month_expr = extract("month", DailySummary.date).label("month")

        query = (
            self.db.query(
                year_expr,
                month_expr,
                func.coalesce(func.sum(DailySummary.total_in), 0).label("total_in"),
                func.coalesce(func.sum(DailySummary.total_out), 0).label("total_out"),
            )
            .group_by(year_expr, month_expr)
            .order_by(year_expr.desc(), month_expr.desc())
        )

        if year is not None:
            query = query.filter(extract("year", DailySummary.date) == year)
        if camera_id is not None:
            query = query.filter(DailySummary.camera_id == camera_id)

        total = query.count()
        rows = query.offset(skip).limit(limit).all()

        items = [
            MonthlyRow(
                year=int(row.year),
                month=int(row.month),
                total_in=int(row.total_in),
                total_out=int(row.total_out),
            )
            for row in rows
        ]
        return items, total

    def get_camera_period_totals(
        self,
        camera_id: int,
        start_date: date,
        end_date: date,
    ) -> CountTotals:
        row = (
            self.db.query(
                func.coalesce(func.sum(DailySummary.total_in), 0).label("total_in"),
                func.coalesce(func.sum(DailySummary.total_out), 0).label("total_out"),
            )
            .filter(
                DailySummary.camera_id == camera_id,
                DailySummary.date >= start_date,
                DailySummary.date <= end_date,
            )
            .one()
        )
        return CountTotals(total_in=int(row.total_in), total_out=int(row.total_out))
