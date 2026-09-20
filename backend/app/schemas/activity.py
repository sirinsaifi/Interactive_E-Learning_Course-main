"""Pydantic schemas for interactive activities.

Three activity kinds share one table with a JSON payload. The schema layer
enforces shape rules per kind so the storage column stays trusted.
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

from app.models.activity import (
    ACTIVITY_FLASHCARDS,
    ACTIVITY_MATCHING,
    ACTIVITY_ORDERING,
)
from app.schemas.common import ORMModel


# ---- Per-kind payload schemas ----


class MatchingPair(BaseModel):
    left: str = Field(..., min_length=1, max_length=255)
    right: str = Field(..., min_length=1, max_length=255)


class MatchingPayload(BaseModel):
    pairs: List[MatchingPair] = Field(..., min_length=2, max_length=12)


class Flashcard(BaseModel):
    front: str = Field(..., min_length=1, max_length=500)
    back: str = Field(..., min_length=1, max_length=1000)


class FlashcardsPayload(BaseModel):
    cards: List[Flashcard] = Field(..., min_length=1, max_length=30)


class OrderingPayload(BaseModel):
    # Items are stored in correct order; the learner shuffles them.
    items: List[str] = Field(..., min_length=2, max_length=15)

    @field_validator("items")
    @classmethod
    def _strip_items(cls, v: List[str]) -> List[str]:
        cleaned = [s.strip() for s in v]
        if any(not s for s in cleaned):
            raise ValueError("ordering items must be non-empty strings")
        if len(cleaned) > len(set(cleaned)):
            raise ValueError("ordering items must be unique")
        return cleaned


AnyPayload = Union[MatchingPayload, FlashcardsPayload, OrderingPayload]


def _validate_payload(kind: str, raw: dict) -> dict:
    """Validate `raw` against the schema matching `kind` and return a dict."""
    if kind == ACTIVITY_MATCHING:
        return MatchingPayload.model_validate(raw).model_dump()
    if kind == ACTIVITY_FLASHCARDS:
        return FlashcardsPayload.model_validate(raw).model_dump()
    if kind == ACTIVITY_ORDERING:
        return OrderingPayload.model_validate(raw).model_dump()
    raise ValueError(f"Unsupported activity kind: {kind}")


# ---- Wire shapes ----


ActivityKind = Literal["matching", "flashcards", "ordering"]


class ActivityRead(ORMModel):
    id: int
    section_id: int
    kind: ActivityKind
    title: str
    instructions: Optional[str] = None
    position: int
    payload: dict
    created_at: datetime
    updated_at: datetime


class ActivitySummary(ORMModel):
    """Lightweight pointer embedded into SectionRead."""

    id: int
    kind: ActivityKind
    title: str
    position: int


class ActivityCreate(BaseModel):
    kind: ActivityKind
    title: Annotated[str, Field(min_length=1, max_length=255)]
    instructions: Optional[Annotated[str, Field(max_length=1000)]] = None
    payload: dict
    position: Optional[int] = Field(default=None, ge=0)

    @field_validator("payload")
    @classmethod
    def _payload_is_dict(cls, v):
        if not isinstance(v, dict):
            raise ValueError("payload must be an object")
        return v


class ActivityUpdate(BaseModel):
    title: Optional[Annotated[str, Field(min_length=1, max_length=255)]] = None
    instructions: Optional[Annotated[str, Field(max_length=1000)]] = None
    payload: Optional[dict] = None
    position: Optional[int] = Field(default=None, ge=0)
