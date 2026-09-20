"""add courses.instructor_id

Revision ID: 0007_course_instructor
Revises: 0006_quizzes
Create Date: 2026-06-28 14:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_course_instructor"
down_revision: Union[str, None] = "0006_quizzes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column("instructor_id", sa.BigInteger(), nullable=True),
    )
    op.create_index("ix_courses_instructor_id", "courses", ["instructor_id"])
    op.create_foreign_key(
        "fk_courses_instructor_user",
        "courses",
        "users",
        ["instructor_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_courses_instructor_user", "courses", type_="foreignkey")
    op.drop_index("ix_courses_instructor_id", table_name="courses")
    op.drop_column("courses", "instructor_id")
