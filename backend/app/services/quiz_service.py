"""Quiz service — fetches quizzes, grades attempts, supports instructor editing."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.quiz import Quiz, QuizAttempt, QuizQuestion
from app.repositories.quiz_repository import QuizRepository
from app.schemas.quiz import (
    QuizAttemptRead,
    QuizEditView,
    QuizQuestionEdit,
    QuizQuestionRead,
    QuizQuestionResult,
    QuizRead,
    QuizQuestionUpdate,
    QuizUpdate,
)


class QuizService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = QuizRepository(db)

    # ---- Reads (learner-facing, no answers) ----

    def get_quiz_for_section(self, section_id: int) -> QuizRead:
        quiz = self.repo.get_by_section_id(section_id)
        if quiz is None:
            raise NotFoundError(f"No quiz for section {section_id}")
        return self._to_read(quiz)

    def get_quiz(self, quiz_id: int) -> QuizRead:
        quiz = self.repo.get(quiz_id)
        if quiz is None:
            raise NotFoundError(f"Quiz {quiz_id} not found")
        return self._to_read(quiz)

    def get_my_latest_attempt(
        self, *, user_id: int, quiz_id: int
    ) -> Optional[QuizAttemptRead]:
        quiz = self.repo.get(quiz_id)
        if quiz is None:
            raise NotFoundError(f"Quiz {quiz_id} not found")
        attempt = self.repo.latest_attempt(user_id=user_id, quiz_id=quiz_id)
        if attempt is None:
            return None
        return self._attempt_to_read(attempt, quiz.questions)

    # ---- Writes (learner) ----

    def submit_attempt(
        self, *, user_id: int, quiz_id: int, answers: list[int]
    ) -> QuizAttemptRead:
        quiz = self.repo.get(quiz_id)
        if quiz is None:
            raise NotFoundError(f"Quiz {quiz_id} not found")

        questions = sorted(quiz.questions, key=lambda q: q.position)
        total = len(questions)

        if len(answers) != total:
            raise ValidationError(
                f"Expected {total} answers, received {len(answers)}"
            )

        score = sum(
            1
            for q, selected in zip(questions, answers)
            if selected == q.correct_index
        )
        percent = int(round((score / total) * 100)) if total else 0
        passed = percent >= quiz.pass_threshold

        attempt = QuizAttempt(
            user_id=user_id,
            quiz_id=quiz_id,
            answers=list(answers),
            score=score,
            total=total,
            passed=passed,
        )
        self.repo.add_attempt(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return self._attempt_to_read(attempt, questions)

    # ---- Instructor editing (answers exposed) ----

    def get_quiz_for_edit(self, quiz_id: int) -> QuizEditView:
        quiz = self.repo.get(quiz_id)
        if quiz is None:
            raise NotFoundError(f"Quiz {quiz_id} not found")
        questions = sorted(quiz.questions, key=lambda q: q.position)
        return QuizEditView(
            id=quiz.id,
            section_id=quiz.section_id,
            title=quiz.title,
            pass_threshold=quiz.pass_threshold,
            questions=[
                QuizQuestionEdit(
                    id=q.id,
                    position=q.position,
                    text=q.text,
                    options=q.options,
                    correct_index=q.correct_index,
                )
                for q in questions
            ],
        )

    def update_quiz_meta(self, quiz_id: int, payload: QuizUpdate) -> QuizEditView:
        quiz = self.repo.get(quiz_id)
        if quiz is None:
            raise NotFoundError(f"Quiz {quiz_id} not found")
        if payload.title is not None:
            quiz.title = payload.title
        if payload.pass_threshold is not None:
            quiz.pass_threshold = payload.pass_threshold
        self.db.commit()
        return self.get_quiz_for_edit(quiz_id)

    def update_question(
        self, *, quiz_id: int, question_id: int, payload: QuizQuestionUpdate
    ) -> QuizQuestionEdit:
        question = self.repo.get_question(question_id)
        if question is None or question.quiz_id != quiz_id:
            raise NotFoundError(f"Question {question_id} not found on quiz {quiz_id}")
        if payload.text is not None:
            question.text = payload.text
        if payload.options is not None:
            question.option_a = payload.options[0]
            question.option_b = payload.options[1]
            question.option_c = payload.options[2]
            question.option_d = payload.options[3]
        if payload.correct_index is not None:
            question.correct_index = payload.correct_index
        self.db.commit()
        self.db.refresh(question)
        return QuizQuestionEdit(
            id=question.id,
            position=question.position,
            text=question.text,
            options=question.options,
            correct_index=question.correct_index,
        )

    # ---- Mapping helpers ----

    @staticmethod
    def _to_read(quiz: Quiz) -> QuizRead:
        questions = sorted(quiz.questions, key=lambda q: q.position)
        return QuizRead(
            id=quiz.id,
            section_id=quiz.section_id,
            title=quiz.title,
            pass_threshold=quiz.pass_threshold,
            questions=[
                QuizQuestionRead(
                    id=q.id,
                    position=q.position,
                    text=q.text,
                    options=q.options,
                )
                for q in questions
            ],
        )

    @staticmethod
    def _attempt_to_read(
        attempt: QuizAttempt, questions: list[QuizQuestion]
    ) -> QuizAttemptRead:
        ordered = sorted(questions, key=lambda q: q.position)
        total = len(ordered)
        percent = int(round((attempt.score / total) * 100)) if total else 0
        answers = list(attempt.answers or [])
        results: list[QuizQuestionResult] = []
        for idx, q in enumerate(ordered):
            selected = answers[idx] if idx < len(answers) else None
            is_correct = selected == q.correct_index
            results.append(
                QuizQuestionResult(
                    question_id=q.id,
                    position=q.position,
                    text=q.text,
                    options=q.options,
                    selected_index=selected,
                    correct_index=q.correct_index,
                    is_correct=is_correct,
                )
            )
        return QuizAttemptRead(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            score=attempt.score,
            total=attempt.total,
            percent=percent,
            passed=attempt.passed,
            taken_at=attempt.taken_at,
            questions=results,
        )
