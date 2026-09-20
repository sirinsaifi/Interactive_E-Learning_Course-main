"""create video_progress

Revision ID: 0003_progress
Revises: 0002_users
Create Date: 2026-06-28 10:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_progress"
down_revision: Union[str, None] = "0002_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "video_progress",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("video_id", sa.BigInteger(), nullable=False),
        sa.Column("position_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("last_watched_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "video_id", name="uq_video_progress_user_video"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_video_progress_user", "video_progress", ["user_id"])
    op.create_index("ix_video_progress_video", "video_progress", ["video_id"])


def downgrade() -> None:
    op.drop_index("ix_video_progress_video", table_name="video_progress")
    op.drop_index("ix_video_progress_user", table_name="video_progress")
    op.drop_table("video_progress")
