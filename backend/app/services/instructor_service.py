"""Instructor service — course / section / video CRUD for instructors and admins.

Authorization rule: every method takes the calling `User` and checks that
the user is either the assigned `instructor_id` on the course, or has the
admin role. Learners cannot reach these routes (gated by `get_current_instructor`),
but we double-check ownership here so instructors can't touch each other's
courses.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.course import Course, Section, Video
from app.models.quiz import Quiz, QuizQuestion
from app.models.user import ROLE_ADMIN, User
from app.repositories.course_repository import CourseRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.course import CourseListItem, CourseRead
from app.schemas.instructor import (
    CourseCreate,
    CourseUpdate,
    SectionCreate,
    SectionUpdate,
    VideoUpdate,
)
from app.services.course_service import (
    _instructor_to_ref,
    _section_to_read,
    _video_to_read,
)
from app.utils.object_storage import get_storage_backend
from app.utils.storage import thumbnail_url

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_ALLOWED_VIDEO_EXTS = {".mp4", ".webm", ".mov", ".mkv", ".m4v"}

# Placeholder questions seeded for every instructor-created section so the
# "Edit quiz" UI is immediately available. The instructor then replaces
# these with real content.
_DUMMY_QUESTIONS: list[dict] = [
    {
        "text": "Replace this with your first question for this section.",
        "options": [
            "Option A — replace me",
            "Option B — replace me",
            "Option C — replace me",
            "Option D — replace me",
        ],
        "correct_index": 0,
    },
    {
        "text": "Replace this with your second question for this section.",
        "options": [
            "Option A — replace me",
            "Option B — replace me",
            "Option C — replace me",
            "Option D — replace me",
        ],
        "correct_index": 0,
    },
    {
        "text": "Replace this with your third question for this section.",
        "options": [
            "Option A — replace me",
            "Option B — replace me",
            "Option C — replace me",
            "Option D — replace me",
        ],
        "correct_index": 0,
    },
    {
        "text": "Replace this with your fourth question for this section.",
        "options": [
            "Option A — replace me",
            "Option B — replace me",
            "Option C — replace me",
            "Option D — replace me",
        ],
        "correct_index": 0,
    },
]


def _slugify(text: str) -> str:
    slug = _SLUG_RE.sub("-", text.strip().lower()).strip("-")
    return slug or "course"


class InstructorService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CourseRepository(db)
        self.video_repo = VideoRepository(db)

    # ---- Authorization helpers ----

    @staticmethod
    def _is_owner_or_admin(course: Course, user: User) -> bool:
        return user.role == ROLE_ADMIN or course.instructor_id == user.id

    def _course_for(self, course_id: int, user: User) -> Course:
        course = self.repo.get_with_content(course_id)
        if course is None:
            raise NotFoundError(f"Course {course_id} not found")
        if not self._is_owner_or_admin(course, user):
            # Hide existence from non-owners.
            raise NotFoundError(f"Course {course_id} not found")
        return course

    def _section_for(self, section_id: int, user: User) -> Section:
        section = self.db.get(Section, section_id)
        if section is None:
            raise NotFoundError(f"Section {section_id} not found")
        course = self.repo.get(section.course_id)
        if course is None or not self._is_owner_or_admin(course, user):
            raise NotFoundError(f"Section {section_id} not found")
        return section

    def _video_for(self, video_id: int, user: User) -> Video:
        video = self.video_repo.get(video_id)
        if video is None:
            raise NotFoundError(f"Video {video_id} not found")
        section = self.db.get(Section, video.section_id)
        if section is None:
            raise NotFoundError(f"Video {video_id} not found")
        course = self.repo.get(section.course_id)
        if course is None or not self._is_owner_or_admin(course, user):
            raise NotFoundError(f"Video {video_id} not found")
        return video

    # ---- Course listing & CRUD ----

    def list_my_courses(self, user: User) -> list[CourseListItem]:
        if user.role == ROLE_ADMIN:
            courses = list(self.db.execute(select(Course).order_by(Course.id.asc())).scalars().all())
        else:
            stmt = (
                select(Course)
                .where(Course.instructor_id == user.id)
                .order_by(Course.id.asc())
            )
            courses = list(self.db.execute(stmt).scalars().all())
        if not courses:
            return []
        aggregates = self.repo.aggregates_for([c.id for c in courses])
        items: list[CourseListItem] = []
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

    def create_course(self, payload: CourseCreate, user: User) -> CourseRead:
        slug = _slugify(payload.slug or payload.title)
        existing = self.db.execute(select(Course).where(Course.slug == slug)).scalar_one_or_none()
        if existing is not None:
            # Append a numeric suffix to keep the slug unique.
            i = 2
            while self.db.execute(select(Course).where(Course.slug == f"{slug}-{i}")).scalar_one_or_none():
                i += 1
            slug = f"{slug}-{i}"

        course = Course(
            title=payload.title,
            slug=slug,
            description=payload.description,
            instructor=payload.instructor or user.name or user.email,
            instructor_id=user.id,
        )
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return self._course_to_read(course)

    def update_course(
        self, course_id: int, payload: CourseUpdate, user: User
    ) -> CourseRead:
        course = self._course_for(course_id, user)
        if payload.title is not None:
            course.title = payload.title
        if payload.description is not None:
            course.description = payload.description
        if payload.instructor is not None:
            course.instructor = payload.instructor
        self.db.commit()
        self.db.refresh(course)
        return self._course_to_read(course)

    def delete_course(self, course_id: int, user: User) -> None:
        course = self._course_for(course_id, user)
        self.db.delete(course)
        self.db.commit()

    def get_my_course(self, course_id: int, user: User) -> CourseRead:
        course = self._course_for(course_id, user)
        return self._course_to_read(course)

    # ---- Section CRUD ----

    def add_section(self, course_id: int, payload: SectionCreate, user: User):
        course = self._course_for(course_id, user)
        next_order = (
            payload.order_index
            if payload.order_index is not None
            else (max((s.order_index for s in course.sections), default=0) + 1)
        )
        section = Section(
            course_id=course.id,
            title=payload.title,
            order_index=next_order,
        )
        self.db.add(section)
        self.db.flush()

        quiz = Quiz(section_id=section.id, title=f"{section.title} quiz")
        self.db.add(quiz)
        self.db.flush()
        for idx, q in enumerate(_DUMMY_QUESTIONS):
            self.db.add(
                QuizQuestion(
                    quiz_id=quiz.id,
                    position=idx,
                    text=q["text"],
                    option_a=q["options"][0],
                    option_b=q["options"][1],
                    option_c=q["options"][2],
                    option_d=q["options"][3],
                    correct_index=q["correct_index"],
                )
            )
        self.db.commit()
        self.db.refresh(section)
        return _section_to_read(section)

    def update_section(
        self, section_id: int, payload: SectionUpdate, user: User
    ):
        section = self._section_for(section_id, user)
        if payload.title is not None:
            section.title = payload.title
        if payload.order_index is not None:
            section.order_index = payload.order_index
        self.db.commit()
        self.db.refresh(section)
        return _section_to_read(section)

    def delete_section(self, section_id: int, user: User) -> None:
        section = self._section_for(section_id, user)
        self.db.delete(section)
        self.db.commit()

    # ---- Video CRUD ----

    def upload_video(
        self,
        section_id: int,
        upload: UploadFile,
        *,
        title: Optional[str],
        description: Optional[str],
        user: User,
    ):
        section = self._section_for(section_id, user)
        course = self.repo.get(section.course_id)
        if course is None:  # pragma: no cover - defensive
            raise NotFoundError(f"Section {section_id} not found")

        filename = upload.filename or "video.mp4"
        ext = Path(filename).suffix.lower()
        if ext not in _ALLOWED_VIDEO_EXTS:
            raise ValidationError(
                f"Unsupported video format '{ext}'. Allowed: "
                + ", ".join(sorted(_ALLOWED_VIDEO_EXTS))
            )

        # Persist via the configured storage backend (local disk or R2).
        section_slug = _slugify(section.title)
        try:
            rel_path = get_storage_backend().save_upload(
                course.slug, section_slug, filename, upload.file
            )
        finally:
            upload.file.close()

        display_title = (title or "").strip() or Path(filename).stem.replace("_", " ").replace("-", " ").title()
        next_order = max((v.order_index for v in section.videos), default=0) + 1
        video = Video(
            section_id=section.id,
            title=display_title,
            description=description,
            file_path=rel_path,
            order_index=next_order,
        )
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        return _video_to_read(video)

    def update_video(self, video_id: int, payload: VideoUpdate, user: User):
        video = self._video_for(video_id, user)
        if payload.title is not None:
            video.title = payload.title
        if payload.description is not None:
            video.description = payload.description
        if payload.order_index is not None:
            video.order_index = payload.order_index
        self.db.commit()
        self.db.refresh(video)
        return _video_to_read(video)

    def delete_video(self, video_id: int, user: User) -> None:
        video = self._video_for(video_id, user)
        # Best-effort file removal; missing files are fine.
        get_storage_backend().delete(video.file_path)
        self.db.delete(video)
        self.db.commit()

    # ---- Admin assignment ----

    def assign_instructor(self, course_id: int, instructor_id: Optional[int]) -> CourseRead:
        course = self.repo.get_with_content(course_id)
        if course is None:
            raise NotFoundError(f"Course {course_id} not found")
        if instructor_id is None:
            course.instructor_id = None
        else:
            user = self.db.get(User, instructor_id)
            if user is None:
                raise NotFoundError(f"User {instructor_id} not found")
            if not user.can_manage_courses:
                raise ConflictError(
                    f"User {instructor_id} must have role 'instructor' or 'admin' before assignment"
                )
            course.instructor_id = instructor_id
            if not course.instructor:
                course.instructor = user.name or user.email
        self.db.commit()
        self.db.refresh(course)
        return self._course_to_read(course)

    # ---- Mapping ----

    @staticmethod
    def _course_to_read(course: Course) -> CourseRead:
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
