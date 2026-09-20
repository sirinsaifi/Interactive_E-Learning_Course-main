"""VideoProgress repository."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.course import Course, Section, Video
from app.models.progress import VideoProgress
from app.repositories.base import BaseRepository


@dataclass(frozen=True)
class CourseProgressRow:
    """Per-course progress aggregate for a single user."""

    course: Course
    total_videos: int
    completed_videos: int
    last_position_seconds: int
    last_video_id: int


class ProgressRepository(BaseRepository[VideoProgress]):
    model = VideoProgress

    def __init__(self, db: Session):
        super().__init__(db, VideoProgress)

    def get_for(self, user_id: int, video_id: int) -> Optional[VideoProgress]:
        stmt = select(VideoProgress).where(
            VideoProgress.user_id == user_id,
            VideoProgress.video_id == video_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_videos(
        self, user_id: int, video_ids: Iterable[int]
    ) -> list[VideoProgress]:
        ids = list(video_ids)
        if not ids:
            return []
        stmt = select(VideoProgress).where(
            VideoProgress.user_id == user_id,
            VideoProgress.video_id.in_(ids),
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_user_courses_with_progress(
        self, user_id: int
    ) -> list[CourseProgressRow]:
        """Return one CourseProgressRow per course the user has any progress on.

        Implemented in two simple steps to keep it portable across MySQL/SQLite.
        """
        # Latest-watched video per course for this user.
        latest_per_course_stmt = (
            select(
                Section.course_id.label("course_id"),
                VideoProgress.video_id,
                VideoProgress.position_seconds,
                VideoProgress.last_watched_at,
            )
            .join(Video, Video.id == VideoProgress.video_id)
            .join(Section, Section.id == Video.section_id)
            .where(VideoProgress.user_id == user_id)
            .order_by(VideoProgress.last_watched_at.desc())
        )
        latest_rows = self.db.execute(latest_per_course_stmt).all()

        latest_by_course_id: dict[int, tuple[int, int]] = {}
        for row in latest_rows:
            if row.course_id not in latest_by_course_id:
                latest_by_course_id[row.course_id] = (row.video_id, row.position_seconds)

        if not latest_by_course_id:
            return []

        course_ids = list(latest_by_course_id)

        # Per-course completion + total counts.
        counts_stmt = (
            select(
                Section.course_id,
                func.count(Video.id).label("total"),
                func.coalesce(
                    func.sum(
                        case((VideoProgress.completed.is_(True), 1), else_=0)
                    ),
                    0,
                ).label("completed"),
            )
            .join(Section, Section.id == Video.section_id)
            .outerjoin(
                VideoProgress,
                (VideoProgress.video_id == Video.id)
                & (VideoProgress.user_id == user_id),
            )
            .where(Section.course_id.in_(course_ids))
            .group_by(Section.course_id)
        )
        counts_by_course_id = {
            row.course_id: (int(row.total), int(row.completed))
            for row in self.db.execute(counts_stmt).all()
        }

        courses = self.db.execute(
            select(Course).where(Course.id.in_(course_ids))
        ).scalars().all()
        course_by_id = {course.id: course for course in courses}

        result: list[CourseProgressRow] = []
        for course_id, (last_video_id, last_position) in latest_by_course_id.items():
            course = course_by_id.get(course_id)
            if course is None:
                continue
            total, completed = counts_by_course_id.get(course_id, (0, 0))
            result.append(
                CourseProgressRow(
                    course=course,
                    total_videos=total,
                    completed_videos=completed,
                    last_position_seconds=last_position,
                    last_video_id=last_video_id,
                )
            )
        return result

    def upsert(
        self,
        *,
        user_id: int,
        video_id: int,
        position_seconds: int,
        completed: bool,
        completed_at,
    ) -> VideoProgress:
        existing = self.get_for(user_id, video_id)
        if existing is None:
            row = VideoProgress(
                user_id=user_id,
                video_id=video_id,
                position_seconds=position_seconds,
                completed=completed,
                completed_at=completed_at,
            )
            self.db.add(row)
            self.db.flush()
            return row

        # Position should only move forward (avoid scrub-back from clobbering).
        if position_seconds > existing.position_seconds:
            existing.position_seconds = position_seconds
        if completed and not existing.completed:
            existing.completed = True
            existing.completed_at = completed_at
        self.db.flush()
        return existing
