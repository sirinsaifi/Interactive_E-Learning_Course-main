"""Progress endpoints — track per-user playback position and completion."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.models.user import User
from app.schemas.progress import (
    CourseProgressItem,
    CourseProgressSummary,
    ProgressUpdate,
    VideoProgressRead,
)
from app.services.progress_service import ProgressService

router = APIRouter(tags=["progress"])


@router.put(
    "/videos/{video_id}/progress",
    response_model=VideoProgressRead,
    summary="Record current playback position for a video",
)
def update_video_progress(
    video_id: int,
    payload: ProgressUpdate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> VideoProgressRead:
    return ProgressService(db).update_video_progress(
        user_id=current_user.id,
        video_id=video_id,
        position_seconds=payload.position_seconds,
        duration_seconds=payload.duration_seconds,
    )


@router.post(
    "/videos/{video_id}/progress/complete",
    response_model=VideoProgressRead,
    status_code=status.HTTP_200_OK,
    summary="Mark a video as completed",
)
def mark_video_complete(
    video_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> VideoProgressRead:
    return ProgressService(db).mark_video_complete(
        user_id=current_user.id, video_id=video_id
    )


@router.get(
    "/courses/{course_id}/progress",
    response_model=CourseProgressSummary,
    summary="Current user's progress for a single course",
)
def get_course_progress(
    course_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> CourseProgressSummary:
    return ProgressService(db).get_course_progress(
        user_id=current_user.id, course_id=course_id
    )


@router.get(
    "/me/progress/courses",
    response_model=list[CourseProgressItem],
    summary="All courses the current user has any progress on",
)
def list_my_course_progress(
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> list[CourseProgressItem]:
    return ProgressService(db).list_my_course_progress(user_id=current_user.id)
