"""Create or adjust sessions table for Phase C.

Revision ID: 015_create_sessions
Revises: 014_create_roadmaps
Create Date: 2026-04-20
"""

from alembic import op

revision = "015_create_sessions"
down_revision = "014_create_roadmaps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("sessions_status_idx", "sessions", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("sessions_status_idx", table_name="sessions")
