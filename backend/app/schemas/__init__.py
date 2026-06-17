from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.count_event import Direction
from app.models.user import UserRole
from app.schemas.camera import (
    CameraCreate,
    CameraReplace,
    CameraResponse,
    CameraUpdate,
)
from app.utils.validators import validate_password_strength


class CountEventBase(BaseModel):
    camera_id: int
    track_id: str = Field(..., min_length=1, max_length=64)
    direction: Direction


class CountEventCreate(CountEventBase):
    timestamp: Optional[datetime] = None


class CountEventResponse(CountEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime


class DailySummaryBase(BaseModel):
    camera_id: int
    date: date
    total_in: int = Field(default=0, ge=0)
    total_out: int = Field(default=0, ge=0)


class DailySummaryCreate(DailySummaryBase):
    pass


class DailySummaryUpdate(BaseModel):
    total_in: Optional[int] = Field(None, ge=0)
    total_out: Optional[int] = Field(None, ge=0)


class DailySummaryResponse(DailySummaryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


__all__ = [
    "CameraCreate",
    "CameraReplace",
    "CameraResponse",
    "CameraUpdate",
    "CountEventCreate",
    "CountEventResponse",
    "DailySummaryCreate",
    "DailySummaryResponse",
    "UserCreate",
    "UserResponse",
]
