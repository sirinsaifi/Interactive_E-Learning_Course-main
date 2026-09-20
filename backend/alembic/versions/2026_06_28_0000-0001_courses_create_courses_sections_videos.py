"""create courses, sections, videos

Revision ID: 0001_courses
Revises:
Create Date: 2026-06-28 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_courses"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructor", sa.String(length=255), nullable=True),
        sa.Column("thumbnail_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_courses_slug"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_courses_slug", "courses", ["slug"], unique=True)

    op.create_table(
        "sections",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_sections_course_id", "sections", ["course_id"])
    op.create_index("ix_sections_course_order", "sections", ["course_id", "order_index"])

    op.create_table(
        "videos",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("section_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_videos_section_id", "videos", ["section_id"])
    op.create_index("ix_videos_section_order", "videos", ["section_id", "order_index"])


def downgrade() -> None:
    op.drop_index("ix_videos_section_order", table_name="videos")
    op.drop_index("ix_videos_section_id", table_name="videos")
    op.drop_table("videos")

    op.drop_index("ix_sections_course_order", table_name="sections")
    op.drop_index("ix_sections_course_id", table_name="sections")
    op.drop_table("sections")

    op.drop_index("ix_courses_slug", table_name="courses")
    op.drop_table("courses")
