"""create quizzes, quiz_questions, quiz_attempts

Revision ID: 0006_quizzes
Revises: 0005_role_learner
Create Date: 2026-06-28 13:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_quizzes"
down_revision: Union[str, None] = "0005_role_learner"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quizzes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("section_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
            server_default="Section quiz",
        ),
        sa.Column(
            "pass_threshold", sa.Integer(), nullable=False, server_default="75"
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("section_id", name="uq_quizzes_section"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("quiz_id", sa.BigInteger(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("text", sa.String(length=1000), nullable=False),
        sa.Column("option_a", sa.String(length=500), nullable=False),
        sa.Column("option_b", sa.String(length=500), nullable=False),
        sa.Column("option_c", sa.String(length=500), nullable=False),
        sa.Column("option_d", sa.String(length=500), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index(
        "ix_quiz_questions_quiz_position",
        "quiz_questions",
        ["quiz_id", "position"],
    )

    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("quiz_id", sa.BigInteger(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column(
            "passed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "taken_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index(
        "ix_quiz_attempts_user_quiz", "quiz_attempts", ["user_id", "quiz_id"]
    )
    op.create_index("ix_quiz_attempts_quiz", "quiz_attempts", ["quiz_id"])


def downgrade() -> None:
    op.drop_index("ix_quiz_attempts_quiz", table_name="quiz_attempts")
    op.drop_index("ix_quiz_attempts_user_quiz", table_name="quiz_attempts")
    op.drop_table("quiz_attempts")
    op.drop_index("ix_quiz_questions_quiz_position", table_name="quiz_questions")
    op.drop_table("quiz_questions")
    op.drop_table("quizzes")
