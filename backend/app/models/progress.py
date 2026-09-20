"""VideoProgress ORM model — per-user watch position and completion state."""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, IdMixin


class VideoProgress(IdMixin, Base):
    __tablename__ = "video_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_video_progress_user_video"),
        Index("ix_video_progress_user", "user_id"),
        Index("ix_video_progress_video", "video_id"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    video_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )
    position_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_watched_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
