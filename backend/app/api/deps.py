"""FastAPI shared dependencies.

Session-token-based auth: the Bearer token is an opaque random string stored
in the users table. No JWT, no OAuth.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import ROLE_INSTRUCTOR, ROLE_ADMIN, User
from app.repositories.user_repository import UserRepository

DBSession = Depends(get_db)


def db_session(db: Session = Depends(get_db)) -> Session:
    return db


_bearer_required = HTTPBearer(auto_error=False, description="Session token")
_bearer_optional = HTTPBearer(auto_error=False, description="Session token (optional)")


def _user_from_credentials(
    credentials: Optional[HTTPAuthorizationCredentials],
    db: Session,
    *,
    required: bool,
) -> Optional[User]:
    if credentials is None or not credentials.credentials:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    token = credentials.credentials
    user = UserRepository(db).get_by_session_token(token)

    if user is None:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_required),
    db: Session = Depends(get_db),
) -> User:
    user = _user_from_credentials(credentials, db, required=True)
    assert user is not None
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_optional),
    db: Session = Depends(get_db),
) -> Optional[User]:
    return _user_from_credentials(credentials, db, required=False)


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin or instructor role (instructors manage the platform)."""
    if not current_user.can_manage_courses:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor or admin role required",
        )
    return current_user


def get_current_instructor(current_user: User = Depends(get_current_user)) -> User:
    """Require instructor or admin role."""
    if current_user.role not in (ROLE_INSTRUCTOR, ROLE_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor role required",
        )
    return current_user
