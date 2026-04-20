"""create cognitive profiles

Revision ID: 004
Revises: 003
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cognitive_profiles",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("cognitive_capacity", sa.Numeric(6, 5), nullable=False),
        sa.Column("attention_stability", sa.Numeric(6, 5), nullable=False),
        sa.Column("learning_tolerance", sa.Numeric(6, 5), nullable=False),
        sa.Column("motor_baseline", sa.Numeric(6, 5), nullable=False),
        sa.Column("stress_resilience", sa.Numeric(6, 5), nullable=False),
        sa.Column("time_constraint", sa.Numeric(6, 5), nullable=False),
        sa.Column("raw_signals", postgresql.JSONB(), nullable=False),
        sa.Column("assessment_metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("cognitive_capacity BETWEEN 0 AND 1", name="cp_cognitive_capacity_check"),
        sa.CheckConstraint("attention_stability BETWEEN 0 AND 1", name="cp_attention_stability_check"),
        sa.CheckConstraint("learning_tolerance BETWEEN 0 AND 1", name="cp_learning_tolerance_check"),
        sa.CheckConstraint("motor_baseline BETWEEN 0 AND 1", name="cp_motor_baseline_check"),
        sa.CheckConstraint("stress_resilience BETWEEN 0 AND 1", name="cp_stress_resilience_check"),
        sa.CheckConstraint("time_constraint BETWEEN 0 AND 1", name="cp_time_constraint_check"),
        sa.UniqueConstraint("user_id", "version", name="cp_user_version_idx"),
    )

    op.create_index("cp_user_id_idx", "cognitive_profiles", ["user_id"])
    op.create_index("cp_created_at_idx", "cognitive_profiles", ["created_at"])


def downgrade() -> None:
    op.drop_index("cp_created_at_idx", table_name="cognitive_profiles")
    op.drop_index("cp_user_id_idx", table_name="cognitive_profiles")
    op.drop_table("cognitive_profiles")
