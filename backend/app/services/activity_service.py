"""Service layer for interactive activities (instructor + learner facing)."""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.activity import (
    ACTIVITY_KINDS,
    ActivityCompletion,
    InteractiveActivity,
)
from app.models.course import Course, Section
from app.models.user import ROLE_ADMIN, User
from app.schemas.activity import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    _validate_payload,
)


def _to_read(row: InteractiveActivity) -> ActivityRead:
    return ActivityRead.model_validate(
        {
            "id": row.id,
            "section_id": row.section_id,
            "kind": row.kind,
            "title": row.title,
            "instructions": row.instructions,
            "position": row.position,
            "payload": row.payload,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
    )


class ActivityService:
    def __init__(self, db: Session):
        self.db = db

    # ---- Ownership helpers ----

    def _section_owned(self, section_id: int, user: User) -> Section:
        section = self.db.get(Section, section_id)
        if section is None:
            raise NotFoundError(f"Section {section_id} not found")
        course = self.db.get(Course, section.course_id)
        if course is None:
            raise NotFoundError(f"Section {section_id} not found")
        if user.role != ROLE_ADMIN and course.instructor_id != user.id:
            raise NotFoundError(f"Section {section_id} not found")
        return section

    def _activity_owned(self, activity_id: int, user: User) -> InteractiveActivity:
        row = self.db.get(InteractiveActivity, activity_id)
        if row is None:
            raise NotFoundError(f"Activity {activity_id} not found")
        # Reuse the section-level ownership check.
        self._section_owned(row.section_id, user)
        return row

    # ---- Reads ----

    def list_for_section(self, section_id: int) -> List[ActivityRead]:
        stmt = (
            select(InteractiveActivity)
            .where(InteractiveActivity.section_id == section_id)
            .order_by(InteractiveActivity.position.asc(), InteractiveActivity.id.asc())
        )
        rows = self.db.execute(stmt).scalars().all()
        return [_to_read(r) for r in rows]

    def get(self, activity_id: int) -> ActivityRead:
        row = self.db.get(InteractiveActivity, activity_id)
        if row is None:
            raise NotFoundError(f"Activity {activity_id} not found")
        return _to_read(row)

    # ---- Instructor mutations ----

    def create(
        self, section_id: int, payload: ActivityCreate, user: User
    ) -> ActivityRead:
        section = self._section_owned(section_id, user)
        if payload.kind not in ACTIVITY_KINDS:
            raise ValidationError(f"Unsupported activity kind: {payload.kind}")
        try:
            cleaned_payload = _validate_payload(payload.kind, payload.payload)
        except Exception as exc:
            raise ValidationError(str(exc))

        if payload.position is None:
            last = self.db.execute(
                select(InteractiveActivity.position)
                .where(InteractiveActivity.section_id == section.id)
                .order_by(InteractiveActivity.position.desc())
                .limit(1)
            ).scalar()
            position = (last or 0) + 1
        else:
            position = payload.position

        row = InteractiveActivity(
            section_id=section.id,
            kind=payload.kind,
            title=payload.title.strip(),
            instructions=(payload.instructions or "").strip() or None,
            position=position,
            payload=cleaned_payload,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _to_read(row)

    def update(
        self, activity_id: int, payload: ActivityUpdate, user: User
    ) -> ActivityRead:
        row = self._activity_owned(activity_id, user)
        if payload.title is not None:
            row.title = payload.title.strip()
        if payload.instructions is not None:
            row.instructions = payload.instructions.strip() or None
        if payload.position is not None:
            row.position = payload.position
        if payload.payload is not None:
            try:
                row.payload = _validate_payload(row.kind, payload.payload)
            except Exception as exc:
                raise ValidationError(str(exc))
        self.db.commit()
        self.db.refresh(row)
        return _to_read(row)

    def delete(self, activity_id: int, user: User) -> None:
        row = self._activity_owned(activity_id, user)
        self.db.delete(row)
        self.db.commit()

    # ---- Learner completion ----

    def mark_complete(self, activity_id: int, user: User) -> datetime:
        """Idempotently record that `user` has finished activity `activity_id`.

        Returns the `completed_at` timestamp of the existing or newly-created
        row. Raises NotFoundError when the activity does not exist.
        """
        activity = self.db.get(InteractiveActivity, activity_id)
        if activity is None:
            raise NotFoundError(f"Activity {activity_id} not found")

        existing = self.db.execute(
            select(ActivityCompletion).where(
                ActivityCompletion.user_id == user.id,
                ActivityCompletion.activity_id == activity_id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing.completed_at

        row = ActivityCompletion(user_id=user.id, activity_id=activity_id)
        self.db.add(row)
        try:
            self.db.commit()
        except IntegrityError:
            # Concurrent insert from another request — swallow and refetch.
            self.db.rollback()
            existing = self.db.execute(
                select(ActivityCompletion).where(
                    ActivityCompletion.user_id == user.id,
                    ActivityCompletion.activity_id == activity_id,
                )
            ).scalar_one()
            return existing.completed_at
        self.db.refresh(row)
        return row.completed_at

    def list_completed_ids_for_activities(
        self, user_id: int, activity_ids: list[int]
    ) -> set[int]:
        if not activity_ids:
            return set()
        rows = self.db.execute(
            select(ActivityCompletion.activity_id).where(
                ActivityCompletion.user_id == user_id,
                ActivityCompletion.activity_id.in_(activity_ids),
            )
        ).all()
        return {r[0] for r in rows}
