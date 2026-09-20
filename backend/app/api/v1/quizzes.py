"""Quiz endpoints (learner-facing).

Instructor-side quiz editing lives in `app.api.v1.instructor`.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.models.quiz import Quiz, QuizAttempt
from app.models.course import Section
from app.models.user import User
from app.schemas.quiz import QuizAttemptRead, QuizAttemptSubmit, QuizRead
from app.services.quiz_service import QuizService

router = APIRouter(tags=["quizzes"])


@router.get(
    "/sections/{section_id}/quiz",
    response_model=QuizRead,
    summary="Get the quiz for a section (no answers)",
)
def get_quiz_for_section(
    section_id: int,
    db: Session = Depends(db_session),
) -> QuizRead:
    return QuizService(db).get_quiz_for_section(section_id)


@router.get(
    "/quizzes/{quiz_id}",
    response_model=QuizRead,
    summary="Get a quiz by id (no answers)",
)
def get_quiz(quiz_id: int, db: Session = Depends(db_session)) -> QuizRead:
    return QuizService(db).get_quiz(quiz_id)


@router.post(
    "/quizzes/{quiz_id}/attempts",
    response_model=QuizAttemptRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an attempt for a quiz",
)
def submit_attempt(
    quiz_id: int,
    payload: QuizAttemptSubmit,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> QuizAttemptRead:
    return QuizService(db).submit_attempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        answers=payload.answers,
    )


@router.get(
    "/quizzes/{quiz_id}/my-attempt",
    response_model=QuizAttemptRead,
    summary="Latest attempt by the current user on this quiz",
)
def get_my_attempt(
    quiz_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> QuizAttemptRead:
    result: Optional[QuizAttemptRead] = QuizService(db).get_my_latest_attempt(
        user_id=current_user.id, quiz_id=quiz_id
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No attempt found"
        )
    return result

@router.get(
    "/courses/{course_id}/passed-quizzes",
    response_model=list[int],
    summary="Quiz IDs the current user has passed for this course",
)
def get_passed_quizzes_for_course(
    course_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> list[int]:
    """Returns a list of quiz IDs that the current user has at least one passing attempt on."""
    from sqlalchemy import select
    # Find all quiz IDs belonging to this course via Section
    quiz_ids_stmt = (
        select(Quiz.id)
        .join(Section, Quiz.section_id == Section.id)
        .where(Section.course_id == course_id)
    )
    all_quiz_ids = set(db.execute(quiz_ids_stmt).scalars().all())
    if not all_quiz_ids:
        return []
    # Among those, find which ones the user has passed
    passed_stmt = (
        select(QuizAttempt.quiz_id)
        .where(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.quiz_id.in_(all_quiz_ids),
            QuizAttempt.passed.is_(True),
        )
        .distinct()
    )
    return list(db.execute(passed_stmt).scalars().all())
