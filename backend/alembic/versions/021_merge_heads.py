"""Merge heads 017_create_checkpoint_states and 020

Revision ID: 021_merge_heads
Revises: 017_create_checkpoint_states, 020
Create Date: 2026-04-20
"""

from alembic import op

revision = "021_merge_heads"
down_revision = ("017_create_checkpoint_states", "020")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
