"""User repository."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower().strip()).first()

    def get_by_session_token(self, token: str) -> Optional[User]:
        return self.db.query(User).filter(User.session_token == token).first()

    def list_all(self) -> list[User]:
        return self.db.query(User).order_by(User.created_at.desc()).all()
