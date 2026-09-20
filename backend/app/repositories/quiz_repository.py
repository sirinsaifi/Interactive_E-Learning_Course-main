"""Quiz repositories — quizzes, questions, and attempts."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.quiz import Quiz, QuizAttempt, QuizQuestion
from app.repositories.base import BaseRepository


class QuizRepository(BaseRepository[Quiz]):
    model = Quiz

    def __init__(self, db: Session):
        super().__init__(db, Quiz)

    def get_by_section_id(self, section_id: int) -> Optional[Quiz]:
        stmt = select(Quiz).where(Quiz.section_id == section_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_questions(self, quiz_id: int) -> list[QuizQuestion]:
        stmt = (
            select(QuizQuestion)
            .where(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.position.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_question(self, question_id: int) -> Optional[QuizQuestion]:
        return self.db.get(QuizQuestion, question_id)

    def latest_attempt(
        self, *, user_id: int, quiz_id: int
    ) -> Optional[QuizAttempt]:
        stmt = (
            select(QuizAttempt)
            .where(QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id)
            .order_by(desc(QuizAttempt.taken_at), desc(QuizAttempt.id))
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()


    def best_attempt(
        self, *, user_id: int, quiz_id: int
    ) -> Optional[QuizAttempt]:
        """Return a passing attempt if one exists, otherwise the latest attempt.

        This prevents a retake-and-fail from revoking an already-earned certificate.
        """
        stmt_pass = (
            select(QuizAttempt)
            .where(
                QuizAttempt.user_id == user_id,
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.passed.is_(True),
            )
            .order_by(desc(QuizAttempt.taken_at), desc(QuizAttempt.id))
            .limit(1)
        )
        passing = self.db.execute(stmt_pass).scalar_one_or_none()
        if passing is not None:
            return passing
        return self.latest_attempt(user_id=user_id, quiz_id=quiz_id)

    def add_attempt(self, attempt: QuizAttempt) -> QuizAttempt:
        return self.add(attempt)
