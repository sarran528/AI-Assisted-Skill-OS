"""create roadmaps

Revision ID: 007
Revises: 006
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roadmaps",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("skill_id", sa.String(length=64), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column("parameters_id", sa.UUID(), sa.ForeignKey("learning_parameters.id"), nullable=False),
        sa.Column("structure", postgresql.JSONB(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("rm_user_skill_idx", "roadmaps", ["user_id", "skill_id", "status"])
    op.create_index("rm_fingerprint_idx", "roadmaps", ["fingerprint"])
    op.create_index("rm_status_idx", "roadmaps", ["status"])


def downgrade() -> None:
    op.drop_index("rm_status_idx", table_name="roadmaps")
    op.drop_index("rm_fingerprint_idx", table_name="roadmaps")
    op.drop_index("rm_user_skill_idx", table_name="roadmaps")
    op.drop_table("roadmaps")
