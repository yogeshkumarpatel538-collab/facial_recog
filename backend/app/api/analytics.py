from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    CameraAnalyticsResponse,
    CountSummary,
    DailyCount,
    HourlyCount,
    MonthlyCount,
    PaginatedResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/today",
    response_model=CountSummary,
    summary="Today's count totals",
    description="Aggregated in/out counts for today or a given date, optionally filtered by camera.",
    responses={401: {"description": "Not authenticated"}, 404: {"description": "Camera not found"}},
)
def get_today_analytics(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    target_date: Optional[date] = Query(None, alias="date", description="Date (defaults to today)"),
    camera_id: Optional[int] = Query(None, ge=1, description="Filter by camera ID"),
):
    return AnalyticsService(db).get_today(target_date=target_date, camera_id=camera_id)


@router.get(
    "/hourly",
    response_model=PaginatedResponse[HourlyCount],
    summary="Hourly count breakdown",
    description="In/out counts grouped by hour for a given date.",
    responses={401: {"description": "Not authenticated"}, 404: {"description": "Camera not found"}},
)
def get_hourly_analytics(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    target_date: Optional[date] = Query(None, alias="date", description="Date (defaults to today)"),
    camera_id: Optional[int] = Query(None, ge=1, description="Filter by camera ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=24),
):
    return AnalyticsService(db).get_hourly(
        target_date=target_date,
        camera_id=camera_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/daily",
    response_model=PaginatedResponse[DailyCount],
    summary="Daily count breakdown",
    description="Paginated daily totals from pre-aggregated summaries. Defaults to last 30 days.",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Camera not found"},
        422: {"description": "Invalid date range"},
    },
)
def get_daily_analytics(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date (inclusive)"),
    camera_id: Optional[int] = Query(None, ge=1, description="Filter by camera ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(31, ge=1, le=366),
):
    return AnalyticsService(db).get_daily(
        start_date=start_date,
        end_date=end_date,
        camera_id=camera_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/monthly",
    response_model=PaginatedResponse[MonthlyCount],
    summary="Monthly count breakdown",
    description="Paginated monthly totals aggregated from daily summaries.",
    responses={401: {"description": "Not authenticated"}, 404: {"description": "Camera not found"}},
)
def get_monthly_analytics(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Filter by year"),
    camera_id: Optional[int] = Query(None, ge=1, description="Filter by camera ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=120),
):
    return AnalyticsService(db).get_monthly(
        year=year,
        camera_id=camera_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/camera/{camera_id}",
    response_model=CameraAnalyticsResponse,
    summary="Analytics for a specific camera",
    description="Period totals and paginated daily breakdown for one camera.",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Camera not found"},
        422: {"description": "Invalid date range"},
    },
)
def get_camera_analytics(
    camera_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date (inclusive)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(31, ge=1, le=366),
):
    return AnalyticsService(db).get_camera_analytics(
        camera_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
