"""create sessions

Revision ID: 008
Revises: 007b
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "008"
down_revision = "007b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("roadmap_id", sa.UUID(), sa.ForeignKey("roadmaps.id"), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("phase", sa.String(length=64), nullable=False),
        sa.Column("technique_id", sa.String(length=64), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("metrics_captured", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("protocol_steps_completed", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("protocol_violations", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("failure_reason", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("sess_roadmap_idx", "sessions", ["roadmap_id"])
    op.create_index("sess_user_status_idx", "sessions", ["user_id", "status"])
    op.create_index("sess_technique_idx", "sessions", ["roadmap_id", "technique_id", "attempt_number"])
    op.create_index("sess_started_at_idx", "sessions", ["started_at"])


def downgrade() -> None:
    op.drop_index("sess_started_at_idx", table_name="sessions")
    op.drop_index("sess_technique_idx", table_name="sessions")
    op.drop_index("sess_user_status_idx", table_name="sessions")
    op.drop_index("sess_roadmap_idx", table_name="sessions")
    op.drop_table("sessions")
