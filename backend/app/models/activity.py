"""Interactive activity ORM model.

A single table backs three activity kinds: drag-and-drop matching, flip
flashcards, and sequence/ordering. Type-specific data lives in the `payload`
JSON column, validated at the schema layer.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.course import Section


ACTIVITY_MATCHING = "matching"
ACTIVITY_FLASHCARDS = "flashcards"
ACTIVITY_ORDERING = "ordering"

ACTIVITY_KINDS = (ACTIVITY_MATCHING, ACTIVITY_FLASHCARDS, ACTIVITY_ORDERING)


class InteractiveActivity(IdMixin, TimestampMixin, Base):
    __tablename__ = "interactive_activities"
    __table_args__ = (
        Index("ix_activities_section_position", "section_id", "position"),
    )

    section_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    section: Mapped["Section"] = relationship(back_populates="activities")


class ActivityCompletion(IdMixin, Base):
    """Marks that a learner has finished a given activity.

    Insert-once (upsert-style): one row per (user_id, activity_id). Kept
    minimal because activities are not scored — completion is binary.
    """

    __tablename__ = "activity_completions"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "activity_id", name="uq_activity_completions_user_activity"
        ),
        Index("ix_activity_completions_user", "user_id"),
        Index("ix_activity_completions_activity", "activity_id"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    activity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("interactive_activities.id", ondelete="CASCADE"),
        nullable=False,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
