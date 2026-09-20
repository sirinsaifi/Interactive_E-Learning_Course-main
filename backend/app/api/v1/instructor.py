"""Instructor endpoints — course / section / video / quiz management.

All routes require role=instructor or role=admin. Each handler additionally
verifies that the calling user owns the target course (admin bypasses this).
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_instructor
from app.core.exceptions import NotFoundError
from app.models.course import Section
from app.models.user import User
from app.schemas.course import CourseListItem, CourseRead, SectionRead, VideoRead
from app.schemas.instructor import (
    CourseCreate,
    CourseUpdate,
    SectionCreate,
    SectionUpdate,
    VideoUpdate,
)
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.schemas.quiz import (
    QuizEditView,
    QuizQuestionEdit,
    QuizQuestionUpdate,
    QuizUpdate,
)
from app.services.activity_service import ActivityService
from app.services.instructor_service import InstructorService
from app.services.quiz_service import QuizService

router = APIRouter(
    prefix="/instructor",
    tags=["instructor"],
    dependencies=[Depends(get_current_instructor)],
)


# ---- Courses ----


@router.get("/courses", response_model=list[CourseListItem], summary="List my courses")
def list_my_courses(
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> list[CourseListItem]:
    return InstructorService(db).list_my_courses(current_user)


@router.post(
    "/courses",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course (owned by me)",
)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> CourseRead:
    return InstructorService(db).create_course(payload, current_user)


@router.get(
    "/courses/{course_id}",
    response_model=CourseRead,
    summary="Get a course I own (admin: any course)",
)
def get_my_course(
    course_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> CourseRead:
    return InstructorService(db).get_my_course(course_id, current_user)


@router.patch(
    "/courses/{course_id}",
    response_model=CourseRead,
    summary="Update course metadata",
)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> CourseRead:
    return InstructorService(db).update_course(course_id, payload, current_user)


@router.delete(
    "/courses/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a course",
)
def delete_course(
    course_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
):
    InstructorService(db).delete_course(course_id, current_user)
    return None


# ---- Sections ----


@router.post(
    "/courses/{course_id}/sections",
    response_model=SectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a section to a course",
)
def add_section(
    course_id: int,
    payload: SectionCreate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> SectionRead:
    return InstructorService(db).add_section(course_id, payload, current_user)


@router.patch(
    "/sections/{section_id}",
    response_model=SectionRead,
    summary="Update a section",
)
def update_section(
    section_id: int,
    payload: SectionUpdate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> SectionRead:
    return InstructorService(db).update_section(section_id, payload, current_user)


@router.delete(
    "/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a section",
)
def delete_section(
    section_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
):
    InstructorService(db).delete_section(section_id, current_user)
    return None


# ---- Videos ----


@router.post(
    "/sections/{section_id}/videos",
    response_model=VideoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new video into a section",
)
def upload_video(
    section_id: int,
    file: UploadFile = File(..., description="Video file (.mp4, .webm, .mov, .mkv, .m4v)"),
    title: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> VideoRead:
    return InstructorService(db).upload_video(
        section_id,
        file,
        title=title,
        description=description,
        user=current_user,
    )


@router.patch(
    "/videos/{video_id}",
    response_model=VideoRead,
    summary="Update video metadata",
)
def update_video(
    video_id: int,
    payload: VideoUpdate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> VideoRead:
    return InstructorService(db).update_video(video_id, payload, current_user)


@router.delete(
    "/videos/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a video",
)
def delete_video(
    video_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
):
    InstructorService(db).delete_video(video_id, current_user)
    return None


# ---- Quiz editing ----


def _ensure_quiz_owned(db: Session, quiz_id: int, user: User) -> None:
    """Refuse access when the calling user does not own the parent course."""
    from app.models.quiz import Quiz

    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise NotFoundError(f"Quiz {quiz_id} not found")
    section = db.get(Section, quiz.section_id)
    if section is None:
        raise NotFoundError(f"Quiz {quiz_id} not found")
    # Reuse instructor service ownership rule.
    svc = InstructorService(db)
    course = svc.repo.get(section.course_id)
    if course is None or not InstructorService._is_owner_or_admin(course, user):
        raise NotFoundError(f"Quiz {quiz_id} not found")


@router.get(
    "/quizzes/{quiz_id}",
    response_model=QuizEditView,
    summary="Get a quiz for editing (includes correct answers)",
)
def get_quiz_for_edit(
    quiz_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> QuizEditView:
    _ensure_quiz_owned(db, quiz_id, current_user)
    return QuizService(db).get_quiz_for_edit(quiz_id)


@router.patch(
    "/quizzes/{quiz_id}",
    response_model=QuizEditView,
    summary="Update quiz title or pass threshold",
)
def update_quiz_meta(
    quiz_id: int,
    payload: QuizUpdate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> QuizEditView:
    _ensure_quiz_owned(db, quiz_id, current_user)
    return QuizService(db).update_quiz_meta(quiz_id, payload)


@router.patch(
    "/quizzes/{quiz_id}/questions/{question_id}",
    response_model=QuizQuestionEdit,
    summary="Update one quiz question (text, options, correct answer)",
)
def update_quiz_question(
    quiz_id: int,
    question_id: int,
    payload: QuizQuestionUpdate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> QuizQuestionEdit:
    _ensure_quiz_owned(db, quiz_id, current_user)
    return QuizService(db).update_question(
        quiz_id=quiz_id, question_id=question_id, payload=payload
    )


# ---- Interactive activities ----


@router.get(
    "/sections/{section_id}/activities",
    response_model=list[ActivityRead],
    summary="List activities in a section (instructor view)",
)
def list_section_activities(
    section_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> list[ActivityRead]:
    svc = ActivityService(db)
    svc._section_owned(section_id, current_user)
    return svc.list_for_section(section_id)


@router.post(
    "/sections/{section_id}/activities",
    response_model=ActivityRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new interactive activity in a section",
)
def create_activity(
    section_id: int,
    payload: ActivityCreate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> ActivityRead:
    return ActivityService(db).create(section_id, payload, current_user)


@router.patch(
    "/activities/{activity_id}",
    response_model=ActivityRead,
    summary="Update an interactive activity",
)
def update_activity(
    activity_id: int,
    payload: ActivityUpdate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
) -> ActivityRead:
    return ActivityService(db).update(activity_id, payload, current_user)


@router.delete(
    "/activities/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an interactive activity",
)
def delete_activity(
    activity_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_instructor),
):
    ActivityService(db).delete(activity_id, current_user)
    return None
