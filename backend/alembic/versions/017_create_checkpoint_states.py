"""Create checkpoint states table.

Revision ID: 017_create_checkpoint_states
Revises: 016_create_evidence
Create Date: 2026-04-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "017_create_checkpoint_states"
down_revision = "016_create_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "checkpoint_states",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("roadmap_id", sa.UUID(), sa.ForeignKey("roadmaps.id"), nullable=False),
        sa.Column("phase_slug", sa.String(length=64), nullable=False),
        sa.Column("checkpoint_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_result", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("checkpoint_states_roadmap_phase_idx", "checkpoint_states", ["roadmap_id", "phase_slug"], unique=False)
    op.create_index("checkpoint_states_lookup_idx", "checkpoint_states", ["roadmap_id", "checkpoint_id"], unique=False)


def downgrade() -> None:
    op.drop_index("checkpoint_states_lookup_idx", table_name="checkpoint_states")
    op.drop_index("checkpoint_states_roadmap_phase_idx", table_name="checkpoint_states")
    op.drop_table("checkpoint_states")
