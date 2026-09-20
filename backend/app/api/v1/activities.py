"""Public (learner-facing) interactive activity endpoints.

Returns full payloads so learners can play them. No answer-hiding is required
— matching pairs, flashcard backs, and ordering sequences are the content the
learner is meant to see while attempting the activity.
"""
from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.models.user import User
from app.schemas.activity import ActivityRead
from app.services.activity_service import ActivityService

router = APIRouter(tags=["activities"])


class ActivityCompletionResult(BaseModel):
    activity_id: int
    completed_at: str


@router.get(
    "/sections/{section_id}/activities",
    response_model=List[ActivityRead],
    summary="List interactive activities for a section",
)
def list_activities(
    section_id: int,
    db: Session = Depends(db_session),
) -> List[ActivityRead]:
    return ActivityService(db).list_for_section(section_id)


@router.get(
    "/activities/{activity_id}",
    response_model=ActivityRead,
    summary="Get a single activity by id",
)
def get_activity(
    activity_id: int,
    db: Session = Depends(db_session),
) -> ActivityRead:
    return ActivityService(db).get(activity_id)


@router.post(
    "/activities/{activity_id}/complete",
    response_model=ActivityCompletionResult,
    status_code=status.HTTP_200_OK,
    summary="Mark this activity as completed by the current user (idempotent)",
)
def complete_activity(
    activity_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> ActivityCompletionResult:
    ts = ActivityService(db).mark_complete(activity_id, current_user)
    return ActivityCompletionResult(
        activity_id=activity_id,
        completed_at=ts.isoformat(),
    )
