"""Progress service — write/read user progress for videos and courses."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.course_repository import CourseRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.progress import (
    CourseProgressItem,
    CourseProgressSummary,
    VideoProgressRead,
)
from app.utils.storage import thumbnail_url

# Fraction of a video that counts as "completed" when reached.
COMPLETION_THRESHOLD = 0.9


class ProgressService:
    def __init__(self, db: Session):
        self.db = db
        self.progress_repo = ProgressRepository(db)
        self.video_repo = VideoRepository(db)
        self.course_repo = CourseRepository(db)

    def update_video_progress(
        self,
        *,
        user_id: int,
        video_id: int,
        position_seconds: int,
        duration_seconds: Optional[int],
    ) -> VideoProgressRead:
        video = self.video_repo.get(video_id)
        if video is None:
            raise NotFoundError(f"Video {video_id} not found")

        # Trust the DB-known duration if available, else fall back to client hint.
        effective_duration = video.duration_seconds or duration_seconds

        clamped = max(0, int(position_seconds))
        if effective_duration:
            clamped = min(clamped, int(effective_duration))

        completed = False
        completed_at: Optional[datetime] = None
        if effective_duration and clamped >= int(effective_duration * COMPLETION_THRESHOLD):
            completed = True
            completed_at = datetime.utcnow()

        row = self.progress_repo.upsert(
            user_id=user_id,
            video_id=video_id,
            position_seconds=clamped,
            completed=completed,
            completed_at=completed_at,
        )
        self.db.commit()
        return self._row_to_read(row)

    def mark_video_complete(self, *, user_id: int, video_id: int) -> VideoProgressRead:
        video = self.video_repo.get(video_id)
        if video is None:
            raise NotFoundError(f"Video {video_id} not found")
        row = self.progress_repo.upsert(
            user_id=user_id,
            video_id=video_id,
            position_seconds=int(video.duration_seconds or 0),
            completed=True,
            completed_at=datetime.utcnow(),
        )
        self.db.commit()
        return self._row_to_read(row)

    def get_course_progress(self, *, user_id: int, course_id: int) -> CourseProgressSummary:
        course = self.course_repo.get_with_content(course_id)
        if course is None:
            raise NotFoundError(f"Course {course_id} not found")

        video_ids = [video.id for section in course.sections for video in section.videos]
        rows = self.progress_repo.list_for_videos(user_id, video_ids)

        total = len(video_ids)
        completed = sum(1 for row in rows if row.completed)
        percent = int(round((completed / total) * 100)) if total else 0

        latest = max(rows, key=lambda row: row.last_watched_at, default=None)
        last_video_id = latest.video_id if latest else None
        last_position = latest.position_seconds if latest else 0

        return CourseProgressSummary(
            course_id=course.id,
            total_videos=total,
            completed_videos=completed,
            percent_complete=percent,
            last_video_id=last_video_id,
            last_position_seconds=last_position,
            videos=[self._row_to_read(row) for row in rows],
        )

    def list_my_course_progress(self, *, user_id: int) -> list[CourseProgressItem]:
        items: list[CourseProgressItem] = []
        for entry in self.progress_repo.list_user_courses_with_progress(user_id):
            total = entry.total_videos
            completed = entry.completed_videos
            percent = int(round((completed / total) * 100)) if total else 0

            last_row = self.progress_repo.get_for(user_id, entry.last_video_id)

            items.append(
                CourseProgressItem(
                    course_id=entry.course.id,
                    course_title=entry.course.title,
                    course_slug=entry.course.slug,
                    thumbnail_url=thumbnail_url(entry.course.thumbnail_path),
                    total_videos=total,
                    completed_videos=completed,
                    percent_complete=percent,
                    last_video_id=entry.last_video_id,
                    last_watched_at=last_row.last_watched_at if last_row else None,
                )
            )
        # Newest activity first.
        items.sort(key=lambda item: item.last_watched_at or datetime.min, reverse=True)
        return items

    @staticmethod
    def _row_to_read(row) -> VideoProgressRead:
        return VideoProgressRead(
            video_id=row.video_id,
            position_seconds=row.position_seconds,
            completed=row.completed,
            completed_at=row.completed_at,
            last_watched_at=row.last_watched_at,
        )
