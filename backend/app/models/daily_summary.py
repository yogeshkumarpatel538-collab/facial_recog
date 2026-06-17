from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.camera import Camera


class DailySummary(Base):
    __tablename__ = "daily_summaries"
    __table_args__ = (
        UniqueConstraint("camera_id", "date", name="uq_daily_summary_camera_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_in: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_out: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    camera: Mapped["Camera"] = relationship(back_populates="daily_summaries")

    def __repr__(self) -> str:
        return (
            f"<DailySummary(id={self.id}, camera_id={self.camera_id}, "
            f"date={self.date}, in={self.total_in}, out={self.total_out})>"
        )
