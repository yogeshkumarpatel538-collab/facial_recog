import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.camera import Camera


class Direction(str, enum.Enum):
    IN = "in"
    OUT = "out"


class CountEvent(Base):
    __tablename__ = "count_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    track_id: Mapped[str] = mapped_column(String(64), nullable=False)
    direction: Mapped[Direction] = mapped_column(
        Enum(Direction, name="direction_enum"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    camera: Mapped["Camera"] = relationship(back_populates="count_events")

    def __repr__(self) -> str:
        return (
            f"<CountEvent(id={self.id}, camera_id={self.camera_id}, "
            f"direction={self.direction.value}, track_id={self.track_id!r})>"
        )
