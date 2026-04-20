"""create evidence

Revision ID: 009
Revises: 008
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", sa.UUID(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("checkpoint_id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("artifact_url", sa.Text(), nullable=True),
        sa.Column("artifact_key", sa.Text(), nullable=True),
        sa.Column("mime_type", sa.String(length=64), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("validated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("validation_result", postgresql.JSONB(), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("file_size_bytes <= 52428800", name="evidence_file_size_check"),
    )

    op.create_index("ev_session_idx", "evidence", ["session_id"])
    op.create_index("ev_checkpoint_idx", "evidence", ["session_id", "checkpoint_id"])
    op.create_index("ev_validated_idx", "evidence", ["validated"])
    op.create_index("ev_user_idx", "evidence", ["user_id"])


def downgrade() -> None:
    op.drop_index("ev_user_idx", table_name="evidence")
    op.drop_index("ev_validated_idx", table_name="evidence")
    op.drop_index("ev_checkpoint_idx", table_name="evidence")
    op.drop_index("ev_session_idx", table_name="evidence")
    op.drop_table("evidence")
