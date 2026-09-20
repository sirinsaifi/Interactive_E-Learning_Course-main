"""rename role 'user' to 'learner'

Revision ID: 0005_role_learner
Revises: 0004_user_role
Create Date: 2026-06-28 12:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_role_learner"
down_revision: Union[str, None] = "0004_user_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Backfill existing rows.
    op.execute("UPDATE users SET role = 'learner' WHERE role = 'user'")
    # Change the column-level default for future inserts.
    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=16),
        existing_nullable=False,
        server_default="learner",
    )


def downgrade() -> None:
    op.execute("UPDATE users SET role = 'user' WHERE role = 'learner'")
    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=16),
        existing_nullable=False,
        server_default="user",
    )
