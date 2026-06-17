from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas import (
    CountEventCreate,
    CountEventResponse,
    DailySummaryCreate,
    DailySummaryResponse,
    UserCreate,
    UserResponse,
)
from app.services import CountEventService, DailySummaryService, UserService

router = APIRouter()


@router.get("/health", tags=["System"])
def health_check():
    """Public health check endpoint."""
    return {"status": "ok"}


@router.post(
    "/count-events",
    response_model=CountEventResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Count Events"],
    summary="Record a count event",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Camera not found"},
    },
)
def record_count_event(
    payload: CountEventCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return CountEventService(db).record_event(payload)


@router.get(
    "/cameras/{camera_id}/events",
    response_model=List[CountEventResponse],
    tags=["Count Events"],
    summary="List count events for a camera",
    responses={401: {"description": "Not authenticated"}},
)
def list_count_events(
    camera_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    return CountEventService(db).list_events(camera_id, skip=skip, limit=limit)


@router.get(
    "/cameras/{camera_id}/summaries",
    response_model=List[DailySummaryResponse],
    tags=["Count Events"],
    summary="List daily summaries for a camera",
    responses={401: {"description": "Not authenticated"}},
)
def list_daily_summaries(
    camera_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return DailySummaryService(db).list_summaries(camera_id)


@router.post(
    "/summaries",
    response_model=DailySummaryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Count Events"],
    summary="Create or update a daily summary (Admin only)",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Camera not found"},
    },
)
def upsert_daily_summary(
    payload: DailySummaryCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return DailySummaryService(db).create_or_update_summary(payload)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
    summary="Create a user (Admin only)",
    description="Admin endpoint to create users with any role.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin privileges required"},
        409: {"description": "Email already registered"},
    },
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return UserService(db).create_user(payload)


@router.get(
    "/users",
    response_model=List[UserResponse],
    tags=["Users"],
    summary="List all users (Admin only)",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin privileges required"},
    },
)
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return UserService(db).list_users()
