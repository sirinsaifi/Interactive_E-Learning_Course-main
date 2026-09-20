"""User-related Pydantic schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.schemas.common import ORMModel


class UserRead(ORMModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    picture_url: Optional[str] = None
    role: str = "learner"
    created_at: datetime
    updated_at: datetime


class EmailLoginRequest(BaseModel):
    """Request body for email-based login."""
    email: EmailStr


class LoginResponse(BaseModel):
    """Returned after a successful login."""
    access_token: str
    token_type: str = "bearer"
    user: UserRead
