"""Pydantic schemas package (request/response DTOs)."""
from app.schemas.common import ErrorResponse, HealthResponse, Message
from app.schemas.course import CourseListItem, CourseRead, SectionRead, VideoRead
from app.schemas.user import EmailLoginRequest, LoginResponse, UserRead

__all__ = [
    "ErrorResponse",
    "HealthResponse",
    "Message",
    "CourseListItem",
    "CourseRead",
    "SectionRead",
    "VideoRead",
    "EmailLoginRequest",
    "LoginResponse",
    "UserRead",
]
