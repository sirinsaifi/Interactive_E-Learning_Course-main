"""Course service — orchestrates repositories and shapes API responses."""
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.course import Course
from app.repositories.course_repository import CourseRepository
from app.schemas.activity import ActivitySummary
from app.schemas.course import (
    CourseListItem,
    CourseRead,
    InstructorRef,
    SectionQuizSummary,
    SectionRead,
    VideoRead,
)
from app.utils.storage import thumbnail_url


def _video_to_read(course_video) -> VideoRead:  # type: ignore[no-untyped-def]
    ext = Path(course_video.file_path).suffix.lower() if course_video.file_path else ""
    content_type = "html" if ext == ".html" else "video"
    return VideoRead.model_validate(
        {
            "id": course_video.id,
            "section_id": course_video.section_id,
            "title": course_video.title,
            "description": course_video.description,
            "duration_seconds": course_video.duration_seconds,
            "order_index": course_video.order_index,
            "content_type": content_type,
            "stream_url": f"/api/v1/videos/{course_video.id}/stream",
            "created_at": course_video.created_at,
            "updated_at": course_video.updated_at,
        }
    )


def _instructor_to_ref(user) -> InstructorRef | None:  # type: ignore[no-untyped-def]
    if user is None:
        return None
    return InstructorRef(
        id=user.id,
        name=user.name,
        email=user.email,
        picture_url=user.picture_url,
    )


def _section_to_read(section) -> SectionRead:  # type: ignore[no-untyped-def]
    quiz_summary: SectionQuizSummary | None = None
    if section.quiz is not None:
        quiz_summary = SectionQuizSummary(
            id=section.quiz.id,
            question_count=len(section.quiz.questions),
            pass_threshold=section.quiz.pass_threshold,
        )
    activities = [
        ActivitySummary(
            id=a.id,
            kind=a.kind,
            title=a.title,
            position=a.position,
        )
        for a in sorted(section.activities or [], key=lambda x: (x.position, x.id))
    ]
    return SectionRead(
        id=section.id,
        course_id=section.course_id,
        title=section.title,
        order_index=section.order_index,
        videos=[_video_to_read(v) for v in section.videos],
        quiz=quiz_summary,
        activities=activities,
    )


class CourseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CourseRepository(db)

    def list_courses(self, *, page: int = 1, page_size: int = 50) -> List[CourseListItem]:
        offset = max(page - 1, 0) * page_size
        courses = self.repo.list_all(offset=offset, limit=page_size)
        if not courses:
            return []
        aggregates = self.repo.aggregates_for([c.id for c in courses])
        items: List[CourseListItem] = []
        for c in courses:
            agg = aggregates.get(
                c.id,
                {"section_count": 0, "video_count": 0, "total_duration_seconds": 0},
            )
            items.append(
                CourseListItem(
                    id=c.id,
                    title=c.title,
                    slug=c.slug,
                    instructor=c.instructor,
                    description=c.description,
                    thumbnail_url=thumbnail_url(c.thumbnail_path),
                    section_count=agg["section_count"],
                    video_count=agg["video_count"],
                    total_duration_seconds=agg["total_duration_seconds"],
                    instructor_id=c.instructor_id,
                    instructor_user=_instructor_to_ref(c.instructor_user),
                )
            )
        return items

    def get_course(self, course_id: int) -> CourseRead:
        course: Course | None = self.repo.get_with_content(course_id)
        if course is None:
            raise NotFoundError(f"Course {course_id} not found")

        return CourseRead(
            id=course.id,
            title=course.title,
            slug=course.slug,
            instructor=course.instructor,
            description=course.description,
            thumbnail_url=thumbnail_url(course.thumbnail_path),
            sections=[_section_to_read(s) for s in course.sections],
            instructor_id=course.instructor_id,
            instructor_user=_instructor_to_ref(course.instructor_user),
            created_at=course.created_at,
            updated_at=course.updated_at,
        )
