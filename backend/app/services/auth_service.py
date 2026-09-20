"""Auth service — email-based login, no OAuth, no JWT."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import generate_session_token
from app.models.user import ROLE_INSTRUCTOR, ROLE_LEARNER, User
from app.repositories.user_repository import UserRepository
from app.schemas.user import LoginResponse, UserRead

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def login_with_email(self, email: str) -> LoginResponse:
        """Find or create a user by email, assign role, return session token."""
        email = email.lower().strip()

        # Determine role: instructor if email matches INSTRUCTOR_EMAIL, else learner.
        instructor_email = settings.INSTRUCTOR_EMAIL.lower().strip()
        role = ROLE_INSTRUCTOR if (instructor_email and email == instructor_email) else ROLE_LEARNER

        user = self.users.get_by_email(email)
        if user is None:
            user = User(
                email=email,
                name=None,
                picture_url=None,
                role=role,
            )
            self.db.add(user)
            logger.info("New user created: %s (role=%s)", email, role)
        else:
            # Always refresh the role on login so that changing INSTRUCTOR_EMAIL takes effect.
            if user.role != role:
                logger.info("Updating role for %s: %s → %s", email, user.role, role)
                user.role = role

        # Rotate the session token on every login.
        token = generate_session_token()
        user.session_token = token

        self.db.commit()
        self.db.refresh(user)

        return LoginResponse(
            access_token=token,
            user=UserRead.model_validate(user),
        )

    def logout(self, user: User) -> None:
        """Invalidate the current session token."""
        user.session_token = None
        self.db.commit()
