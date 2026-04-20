"""Create or adjust evidence table for Phase C.

Revision ID: 016_create_evidence
Revises: 015_create_sessions
Create Date: 2026-04-20
"""

from alembic import op

revision = "016_create_evidence"
down_revision = "015_create_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("evidence_checkpoint_type_idx", "evidence", ["checkpoint_id", "type"], unique=False)


def downgrade() -> None:
    op.drop_index("evidence_checkpoint_type_idx", table_name="evidence")
