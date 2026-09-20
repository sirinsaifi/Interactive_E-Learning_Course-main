"""Shared Pydantic schemas used across endpoints."""
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base schema for models that read from SQLAlchemy ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[object] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    app: str
    version: str
    environment: str
    database: str = Field(examples=["ok", "down"])


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
