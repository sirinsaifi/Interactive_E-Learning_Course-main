"""Course endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.course import CourseListItem, CourseRead
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseListItem], summary="List all courses")
def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(db_session),
) -> list[CourseListItem]:
    return CourseService(db).list_courses(page=page, page_size=page_size)


@router.get("/{course_id}", response_model=CourseRead, summary="Get a course with sections and videos")
def get_course(course_id: int, db: Session = Depends(db_session)) -> CourseRead:
    return CourseService(db).get_course(course_id)
