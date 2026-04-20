"""Create baseline_skill_states table

Revision ID: 007
Revises: 006
Create Date: 2026-04-20

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
        "baseline_skill_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", sa.String(64), nullable=False),
        sa.Column("profile_version", sa.Numeric(5), nullable=False, server_default=sa.text("1")),
        sa.Column("exposure_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("declarative_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("confidence_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("perceived_level", sa.Numeric(5, 4), nullable=False),
        sa.Column("actual_level", sa.Numeric(5, 4), nullable=False),
        sa.Column("confidence_bias", sa.Numeric(6, 5), nullable=False),
        sa.Column("raw_responses", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_baseline_skill_states_user_id"),
        sa.PrimaryKeyConstraint("id", name="pk_baseline_skill_states"),
        sa.CheckConstraint("exposure_score BETWEEN 0 AND 1", name="baseline_exposure_check"),
        sa.CheckConstraint("declarative_score BETWEEN 0 AND 1", name="baseline_declarative_check"),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="baseline_confidence_check"),
        sa.CheckConstraint("perceived_level BETWEEN 0 AND 1", name="baseline_perceived_check"),
        sa.CheckConstraint("actual_level BETWEEN 0 AND 1", name="baseline_actual_check"),
        sa.CheckConstraint("confidence_bias BETWEEN -1 AND 1", name="baseline_bias_check"),
    )


def downgrade() -> None:
    op.drop_table("baseline_skill_states")
