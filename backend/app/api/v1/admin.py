"""Admin-only endpoints. All routes require role=admin."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_admin, get_current_instructor
from app.core.exceptions import NotFoundError
from app.models.course import Course, Section, Video
from app.models.progress import VideoProgress
from app.models.user import ALL_ROLES, User
from app.repositories.user_repository import UserRepository
from app.schemas.course import CourseRead
from app.schemas.instructor import AssignInstructorRequest, RoleAssignRequest
from app.schemas.user import UserRead
from app.services.content_sync_service import SyncStats, sync_content
from app.services.instructor_service import InstructorService

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_instructor)])


class AdminStats(BaseModel):
    users: int
    courses: int
    sections: int
    videos: int
    progress_rows: int


class SyncResponse(BaseModel):
    courses_added: int
    courses_updated: int
    courses_removed: int
    sections_added: int
    sections_removed: int
    videos_added: int
    videos_removed: int
    videos_indexed: int


@router.get("/users", response_model=list[UserRead], summary="List all users")
def list_users(db: Session = Depends(db_session)) -> list[UserRead]:
    rows = UserRepository(db).list_all()
    return [UserRead.model_validate(r) for r in rows]


@router.post(
    "/users/{user_id}/role",
    response_model=UserRead,
    summary="Set a user's role (learner, instructor, admin)",
)
def set_user_role(
    user_id: int,
    payload: RoleAssignRequest,
    db: Session = Depends(db_session),
) -> UserRead:
    if payload.role not in ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Role must be one of: {', '.join(sorted(ALL_ROLES))}",
        )
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} not found")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return UserRead.model_validate(user)


@router.post(
    "/courses/{course_id}/instructor",
    response_model=CourseRead,
    summary="Assign (or clear) the instructor for a course",
)
def assign_course_instructor(
    course_id: int,
    payload: AssignInstructorRequest,
    db: Session = Depends(db_session),
) -> CourseRead:
    return InstructorService(db).assign_instructor(course_id, payload.instructor_id)


@router.get("/stats", response_model=AdminStats, summary="High-level catalog and user stats")
def get_stats(db: Session = Depends(db_session)) -> AdminStats:
    def _count(model) -> int:
        return int(db.execute(select(func.count()).select_from(model)).scalar_one())

    return AdminStats(
        users=_count(User),
        courses=_count(Course),
        sections=_count(Section),
        videos=_count(Video),
        progress_rows=_count(VideoProgress),
    )


@router.post(
    "/content/sync",
    response_model=SyncResponse,
    summary="Force a filesystem→DB content sync",
)
def trigger_sync(
    prune: bool = False,
    db: Session = Depends(db_session),
) -> SyncResponse:
    stats: SyncStats = sync_content(db, prune_missing_courses=prune)
    return SyncResponse(
        courses_added=stats.courses_added,
        courses_updated=stats.courses_updated,
        courses_removed=stats.courses_removed,
        sections_added=stats.sections_added,
        sections_removed=stats.sections_removed,
        videos_added=stats.videos_added,
        videos_removed=stats.videos_removed,
        videos_indexed=stats.videos_indexed,
    )
