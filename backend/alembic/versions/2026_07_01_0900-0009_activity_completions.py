"""create activity_completions

Revision ID: 0009_activity_completions
Revises: 0008_interactive_activities
Create Date: 2026-07-01 09:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_activity_completions"
down_revision: Union[str, None] = "0008_interactive_activities"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "activity_completions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("activity_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["activity_id"], ["interactive_activities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "activity_id",
            name="uq_activity_completions_user_activity",
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index(
        "ix_activity_completions_user", "activity_completions", ["user_id"]
    )
    op.create_index(
        "ix_activity_completions_activity",
        "activity_completions",
        ["activity_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_activity_completions_activity", table_name="activity_completions"
    )
    op.drop_index(
        "ix_activity_completions_user", table_name="activity_completions"
    )
    op.drop_table("activity_completions")
