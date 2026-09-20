"""Pydantic schemas for instructor & admin course management."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(
        default=None,
        max_length=255,
        description="URL slug. If omitted, generated from title.",
    )
    description: Optional[str] = Field(default=None, max_length=10_000)
    instructor: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Display name of the instructor shown to learners.",
    )


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10_000)
    instructor: Optional[str] = Field(default=None, max_length=255)


class SectionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    order_index: Optional[int] = Field(default=None, ge=0)


class SectionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    order_index: Optional[int] = Field(default=None, ge=0)


class VideoUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10_000)
    order_index: Optional[int] = Field(default=None, ge=0)


class AssignInstructorRequest(BaseModel):
    """Admin payload to assign or clear a course's instructor."""

    instructor_id: Optional[int] = Field(
        default=None,
        description="User id to assign as instructor. Pass null to unassign.",
    )

    @field_validator("instructor_id")
    @classmethod
    def _allow_null_or_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("instructor_id must be positive")
        return v


class RoleAssignRequest(BaseModel):
    """Admin payload to set a user's role."""

    role: str = Field(..., description="One of: learner, instructor, admin")
