"""Pydantic schemas for Course / Section / Video."""
from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.schemas.activity import ActivitySummary
from app.schemas.common import ORMModel


class VideoRead(ORMModel):
    id: int
    section_id: int
    title: str
    description: Optional[str] = None
    duration_seconds: Optional[int] = None
    order_index: int
    content_type: str = Field(
        default="video",
        description="'html' for interactive HTML modules, 'video' for media files.",
    )
    stream_url: Optional[str] = Field(
        default=None,
        description="Relative URL for streaming this video (server-populated).",
    )
    created_at: datetime
    updated_at: datetime


class SectionQuizSummary(ORMModel):
    """Lightweight quiz pointer attached to a SectionRead."""

    id: int
    question_count: int
    pass_threshold: int


class SectionRead(ORMModel):
    id: int
    course_id: int
    title: str
    order_index: int
    videos: List[VideoRead] = []
    quiz: Optional[SectionQuizSummary] = None
    activities: List[ActivitySummary] = []


class InstructorRef(ORMModel):
    """Minimal reference to an instructor user."""

    id: int
    name: Optional[str] = None
    email: str
    picture_url: Optional[str] = None


class CourseListItem(ORMModel):
    id: int
    title: str
    slug: str
    instructor: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = Field(
        default=None,
        description="Relative URL to the course thumbnail (server-populated).",
    )
    section_count: int = 0
    video_count: int = 0
    total_duration_seconds: int = 0
    instructor_id: Optional[int] = None
    instructor_user: Optional[InstructorRef] = None


class CourseRead(ORMModel):
    id: int
    title: str
    slug: str
    instructor: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    sections: List[SectionRead] = []
    instructor_id: Optional[int] = None
    instructor_user: Optional[InstructorRef] = None
    created_at: datetime
    updated_at: datetime
