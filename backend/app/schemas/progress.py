"""Pydantic schemas for video / course progress."""
from datetime import datetime
from typing import List, Optional

from pydantic import Field, NonNegativeInt, PositiveInt

from app.schemas.common import ORMModel


class ProgressUpdate(ORMModel):
    """Body for PUT /videos/{id}/progress — a periodic heartbeat from the player."""

    position_seconds: NonNegativeInt = Field(
        ..., description="Current playback position in seconds."
    )
    duration_seconds: Optional[PositiveInt] = Field(
        default=None,
        description="Video duration (sent by the client) used for completion threshold.",
    )


class VideoProgressRead(ORMModel):
    video_id: int
    position_seconds: int
    completed: bool
    completed_at: Optional[datetime] = None
    last_watched_at: datetime


class CourseProgressSummary(ORMModel):
    """Aggregate progress for a single course."""

    course_id: int
    total_videos: int
    completed_videos: int
    percent_complete: int = Field(..., ge=0, le=100)
    last_video_id: Optional[int] = Field(
        default=None,
        description="Most recently watched video in this course, if any.",
    )
    last_position_seconds: int = 0
    videos: List[VideoProgressRead] = []


class CourseProgressItem(ORMModel):
    """Shape used by GET /me/progress/courses (continue-learning list)."""

    course_id: int
    course_title: str
    course_slug: str
    thumbnail_url: Optional[str] = None
    total_videos: int
    completed_videos: int
    percent_complete: int
    last_video_id: Optional[int] = None
    last_watched_at: Optional[datetime] = None
