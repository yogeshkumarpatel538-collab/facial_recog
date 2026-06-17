from datetime import date
from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class CountSummary(BaseModel):
    """Aggregated in/out totals for a period."""

    date: date
    total_in: int = Field(ge=0)
    total_out: int = Field(ge=0)


class HourlyCount(BaseModel):
    hour: int = Field(ge=0, le=23)
    total_in: int = Field(ge=0)
    total_out: int = Field(ge=0)


class DailyCount(BaseModel):
    date: date
    total_in: int = Field(ge=0)
    total_out: int = Field(ge=0)


class MonthlyCount(BaseModel):
    year: int = Field(ge=2000)
    month: int = Field(ge=1, le=12)
    total_in: int = Field(ge=0)
    total_out: int = Field(ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int = Field(ge=0)
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)


class CameraAnalyticsResponse(BaseModel):
    camera_id: int
    camera_name: str
    location: str
    start_date: date
    end_date: date
    total_in: int = Field(ge=0)
    total_out: int = Field(ge=0)
    daily: PaginatedResponse[DailyCount]
