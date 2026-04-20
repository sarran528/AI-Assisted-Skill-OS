"""create doubt log table

Revision ID: 019
Revises: 018
Create Date: 2026-04-20

"""

from alembic import op
import sqlalchemy as sa


revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "doubt_log",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_id", sa.UUID(), sa.ForeignKey("sessions.id"), nullable=True),
        sa.Column("skill_id", sa.String(length=64), nullable=False),
        sa.Column("phase", sa.String(length=64), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("chunks_used", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("doubt_user_created_idx", "doubt_log", ["user_id", "created_at"])
    op.create_index("doubt_session_idx", "doubt_log", ["session_id"])


def downgrade() -> None:
    op.drop_index("doubt_session_idx", table_name="doubt_log")
    op.drop_index("doubt_user_created_idx", table_name="doubt_log")
    op.drop_table("doubt_log")
