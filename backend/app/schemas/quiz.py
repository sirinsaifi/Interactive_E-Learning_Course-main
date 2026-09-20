"""Pydantic schemas for quizzes."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel


# ---- Learner-facing quiz delivery (no answers exposed) ----


class QuizQuestionRead(ORMModel):
    id: int
    position: int
    text: str
    options: List[str]


class QuizRead(ORMModel):
    id: int
    section_id: int
    title: str
    pass_threshold: int
    questions: List[QuizQuestionRead]


# ---- Attempt submission and results ----


class QuizAttemptSubmit(BaseModel):
    answers: List[int] = Field(
        ...,
        description="Selected option index (0-3) per question, in question position order.",
    )

    @field_validator("answers")
    @classmethod
    def _check_answer_range(cls, v: List[int]) -> List[int]:
        for i, a in enumerate(v):
            if not isinstance(a, int) or a < 0 or a > 3:
                raise ValueError(f"answers[{i}] must be an integer 0-3")
        return v


class QuizQuestionResult(BaseModel):
    question_id: int
    position: int
    text: str
    options: List[str]
    selected_index: Optional[int]
    correct_index: int
    is_correct: bool


class QuizAttemptRead(BaseModel):
    id: int
    quiz_id: int
    score: int
    total: int
    percent: int
    passed: bool
    taken_at: datetime
    questions: List[QuizQuestionResult]


# ---- Instructor-facing quiz editing (answers exposed) ----


class QuizQuestionEdit(ORMModel):
    """Full question payload including the correct answer index."""

    id: int
    position: int
    text: str
    options: List[str]
    correct_index: int


class QuizEditView(ORMModel):
    """Editor view of a quiz — exposes correct answers."""

    id: int
    section_id: int
    title: str
    pass_threshold: int
    questions: List[QuizQuestionEdit]


class QuizQuestionUpdate(BaseModel):
    text: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    options: Optional[List[str]] = Field(default=None)
    correct_index: Optional[int] = Field(default=None, ge=0, le=3)

    @field_validator("options")
    @classmethod
    def _check_options(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        if len(v) != 4:
            raise ValueError("options must contain exactly 4 entries")
        for i, opt in enumerate(v):
            if not isinstance(opt, str) or not opt.strip():
                raise ValueError(f"options[{i}] must be a non-empty string")
        return v


class QuizUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    pass_threshold: Optional[int] = Field(default=None, ge=0, le=100)
