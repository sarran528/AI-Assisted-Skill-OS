"""create assessment sessions

Revision ID: 021
Revises: 020
Create Date: 2026-04-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "021"
down_revision = "002_fix_refresh_token_ip_address"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessment_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), nullable=False, unique=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'in_progress'")),
        sa.Column("submissions", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("completed_levels", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("assessment_session_id_idx", "assessment_sessions", ["session_id"])
    op.create_index("assessment_user_status_idx", "assessment_sessions", ["user_id", "status"])


def downgrade() -> None:
    op.drop_index("assessment_user_status_idx", table_name="assessment_sessions")
    op.drop_index("assessment_session_id_idx", table_name="assessment_sessions")
    op.drop_table("assessment_sessions")
