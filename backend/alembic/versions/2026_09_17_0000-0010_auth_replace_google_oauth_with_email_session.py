"""Replace Google OAuth with simple email + session token auth.

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-17 00:00:00.000000

Changes:
- Drop the ``google_sub`` column and its unique index from ``users``.
- Add ``session_token`` column (VARCHAR 64, nullable, unique, indexed).
- Migrate any rows with role='pending' to role='learner'.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0010"
down_revision = "0009_activity_completions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop the google_sub unique constraint / index, then the column.
    with op.batch_alter_table("users", schema=None) as batch_op:
        # Try to drop the index; name may vary across MySQL versions.
        try:
            batch_op.drop_index("ix_users_google_sub")
        except Exception:
            pass
        batch_op.drop_column("google_sub")

    # 2. Add session_token column.
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("session_token", sa.String(length=64), nullable=True)
        )
        batch_op.create_unique_constraint("uq_users_session_token", ["session_token"])
        batch_op.create_index("ix_users_session_token", ["session_token"], unique=True)

    # 3. Promote any 'pending' accounts to 'learner'.
    op.execute("UPDATE users SET role = 'learner' WHERE role = 'pending'")


def downgrade() -> None:
    # Remove session_token.
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_session_token")
        batch_op.drop_constraint("uq_users_session_token", type_="unique")
        batch_op.drop_column("session_token")

    # Re-add google_sub (nullable on downgrade since data is gone).
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("google_sub", sa.String(length=64), nullable=True)
        )
        batch_op.create_index("ix_users_google_sub", ["google_sub"], unique=True)
