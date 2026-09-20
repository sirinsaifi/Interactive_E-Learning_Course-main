"""User model (email-based accounts)."""
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, IdMixin, TimestampMixin

# Allowed role values stored in `users.role`.
ROLE_LEARNER = "learner"
ROLE_INSTRUCTOR = "instructor"
ROLE_ADMIN = "admin"

ALL_ROLES = {ROLE_LEARNER, ROLE_INSTRUCTOR, ROLE_ADMIN}


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    picture_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ROLE_LEARNER, server_default=ROLE_LEARNER
    )
    # Opaque session token – set on login, cleared on logout.
    session_token: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def is_instructor(self) -> bool:
        return self.role == ROLE_INSTRUCTOR

    @property
    def can_manage_courses(self) -> bool:
        return self.role in (ROLE_ADMIN, ROLE_INSTRUCTOR)
