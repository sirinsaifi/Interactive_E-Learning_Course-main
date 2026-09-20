"""Auth endpoints — email-based login and current-user introspection."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.models.user import User
from app.schemas.user import EmailLoginRequest, LoginResponse, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in with an email address — no password required",
)
def login(payload: EmailLoginRequest, db: Session = Depends(db_session)) -> LoginResponse:
    """
    Accepts an email address. If it matches INSTRUCTOR_EMAIL the user gets the
    instructor role; all other addresses become learners. A user row is created
    on first login and reused on subsequent logins.
    """
    return AuthService(db).login_with_email(payload.email)


@router.post(
    "/logout",
    summary="Invalidate the current session token",
)
def logout(
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    AuthService(db).logout(current_user)
    return {"detail": "Logged out successfully"}


@router.get("/me", response_model=UserRead, summary="Get the current authenticated user")
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
