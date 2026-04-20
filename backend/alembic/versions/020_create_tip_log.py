"""create tip log table

Revision ID: 020
Revises: 019
Create Date: 2026-04-20

"""

from alembic import op
import sqlalchemy as sa


revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tip_log",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", sa.UUID(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("technique_id", sa.String(length=64), nullable=False),
        sa.Column("failure_type", sa.String(length=64), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("tip", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("target_step", sa.String(length=64), nullable=True),
        sa.Column("chunks_used", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("tip_session_created_idx", "tip_log", ["session_id", "created_at"])


def downgrade() -> None:
    op.drop_index("tip_session_created_idx", table_name="tip_log")
    op.drop_table("tip_log")
