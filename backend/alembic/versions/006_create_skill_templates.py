"""create skill templates

Revision ID: 006
Revises: 005
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skill_templates",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("skill_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("domain", sa.String(length=64), nullable=False),
        sa.Column("complexity_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("structure", postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("complexity_score BETWEEN 0 AND 1", name="skill_template_complexity_check"),
    )


def downgrade() -> None:
    op.drop_table("skill_templates")
