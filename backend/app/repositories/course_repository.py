"""Course repository — read access to courses, sections, and videos."""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.course import Course, Section, Video
from app.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course]):
    model = Course

    def __init__(self, db: Session):
        super().__init__(db, Course)

    def list_all(self, *, offset: int = 0, limit: int = 50) -> list[Course]:
        stmt = (
            select(Course)
            .order_by(Course.id.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_with_content(self, course_id: int) -> Optional[Course]:
        """Load a course with its sections and videos eagerly."""
        stmt = (
            select(Course)
            .options(selectinload(Course.sections).selectinload(Section.videos))
            .where(Course.id == course_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def aggregates_for(self, course_ids: list[int]) -> dict[int, dict[str, int]]:
        """Return {course_id: {section_count, video_count, total_duration_seconds}}."""
        if not course_ids:
            return {}

        section_counts_stmt = (
            select(Section.course_id, func.count(Section.id))
            .where(Section.course_id.in_(course_ids))
            .group_by(Section.course_id)
        )
        section_counts = dict(self.db.execute(section_counts_stmt).all())

        video_stats_stmt = (
            select(
                Section.course_id,
                func.count(Video.id),
                func.coalesce(func.sum(Video.duration_seconds), 0),
            )
            .join(Section, Section.id == Video.section_id)
            .where(Section.course_id.in_(course_ids))
            .group_by(Section.course_id)
        )
        video_stats = {
            row[0]: (int(row[1]), int(row[2])) for row in self.db.execute(video_stats_stmt).all()
        }

        out: dict[int, dict[str, int]] = {}
        for cid in course_ids:
            vc, dur = video_stats.get(cid, (0, 0))
            out[cid] = {
                "section_count": int(section_counts.get(cid, 0)),
                "video_count": vc,
                "total_duration_seconds": dur,
            }
        return out
