"""Create or adjust roadmaps table for Phase C.

Revision ID: 014_create_roadmaps
Revises: 013_create_skill_research_objects
Create Date: 2026-04-20
"""

from alembic import op
import sqlalchemy as sa

revision = "014_create_roadmaps"
down_revision = "013_create_skill_research_objects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("roadmaps_status_idx", "roadmaps", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("roadmaps_status_idx", table_name="roadmaps")
