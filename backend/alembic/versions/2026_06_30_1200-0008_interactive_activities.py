"""create interactive_activities

Revision ID: 0008_interactive_activities
Revises: 0007_course_instructor
Create Date: 2026-06-30 12:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_interactive_activities"
down_revision: Union[str, None] = "0007_course_instructor"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interactive_activities",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("section_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("instructions", sa.String(length=1000), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["section_id"], ["sections.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index(
        "ix_activities_section_position",
        "interactive_activities",
        ["section_id", "position"],
    )
    op.create_index(
        "ix_interactive_activities_section_id",
        "interactive_activities",
        ["section_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_interactive_activities_section_id",
        table_name="interactive_activities",
    )
    op.drop_index(
        "ix_activities_section_position", table_name="interactive_activities"
    )
    op.drop_table("interactive_activities")
