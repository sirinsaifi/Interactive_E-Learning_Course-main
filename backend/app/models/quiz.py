"""Quiz, QuizQuestion, QuizAttempt ORM models."""
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.course import Section


class Quiz(IdMixin, TimestampMixin, Base):
    __tablename__ = "quizzes"
    __table_args__ = (
        UniqueConstraint("section_id", name="uq_quizzes_section"),
    )

    section_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Section quiz"
    )
    # Percentage (0-100) required to pass.
    pass_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=75)

    questions: Mapped[List["QuizQuestion"]] = relationship(
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="QuizQuestion.position",
        lazy="selectin",
    )
    section: Mapped["Section"] = relationship(back_populates="quiz")


class QuizQuestion(IdMixin, TimestampMixin, Base):
    __tablename__ = "quiz_questions"
    __table_args__ = (
        Index("ix_quiz_questions_quiz_position", "quiz_id", "position"),
    )

    quiz_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    option_a: Mapped[str] = mapped_column(String(500), nullable=False)
    option_b: Mapped[str] = mapped_column(String(500), nullable=False)
    option_c: Mapped[str] = mapped_column(String(500), nullable=False)
    option_d: Mapped[str] = mapped_column(String(500), nullable=False)
    # 0-based index into [option_a, option_b, option_c, option_d].
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")

    @property
    def options(self) -> list[str]:
        return [self.option_a, self.option_b, self.option_c, self.option_d]


class QuizAttempt(IdMixin, Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("ix_quiz_attempts_user_quiz", "user_id", "quiz_id"),
        Index("ix_quiz_attempts_quiz", "quiz_id"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    quiz_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )
    # List of selected option indices (one per question, in position order).
    answers: Mapped[list] = mapped_column(JSON, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    taken_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
