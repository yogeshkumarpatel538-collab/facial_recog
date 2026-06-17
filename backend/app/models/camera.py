from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.count_event import CountEvent
    from app.models.daily_summary import DailySummary


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rtsp_url: Mapped[str] = mapped_column(String(512), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    count_events: Mapped[List["CountEvent"]] = relationship(
        back_populates="camera",
        cascade="all, delete-orphan",
    )
    daily_summaries: Mapped[List["DailySummary"]] = relationship(
        back_populates="camera",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Camera(id={self.id}, name={self.name!r}, location={self.location!r})>"
