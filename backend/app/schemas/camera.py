from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validators import validate_rtsp_url


class CameraBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique display name for the camera",
        examples=["Entrance Cam"],
    )
    rtsp_url: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Stream URL: rtsp://..., rtsps://..., or webcam://0 for laptop camera",
        examples=["rtsp://192.168.1.10:554/stream1", "webcam://0"],
    )
    location: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Physical location of the camera",
        examples=["Main Entrance"],
    )
    active: bool = Field(default=True, description="Whether the camera is actively processing")


class CameraCreate(CameraBase):
    """Schema for creating a new camera."""

    @field_validator("rtsp_url")
    @classmethod
    def validate_rtsp(cls, value: str) -> str:
        return validate_rtsp_url(value)


class CameraReplace(CameraBase):
    """Schema for full camera replacement (PUT)."""

    @field_validator("rtsp_url")
    @classmethod
    def validate_rtsp(cls, value: str) -> str:
        return validate_rtsp_url(value)


class CameraUpdate(BaseModel):
    """Schema for partial camera updates (PATCH)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    rtsp_url: Optional[str] = Field(None, min_length=1, max_length=512)
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    active: Optional[bool] = None

    @field_validator("rtsp_url")
    @classmethod
    def validate_rtsp(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validate_rtsp_url(value)


class CameraResponse(CameraBase):
    """Camera response returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
