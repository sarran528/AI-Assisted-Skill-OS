"""Create skill_research_objects table.

Revision ID: 013_create_skill_research_objects
Revises: 012_create_jobs
Create Date: 2025-04-20 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "013_create_skill_research_objects"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create skill_research_objects table."""
    op.create_table(
        "skill_research_objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", sa.String(64), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_skill_research_objects_skill_id",
        "skill_research_objects",
        ["skill_id"],
        unique=False,
    )
    op.create_index(
        "ix_skill_research_objects_user_id",
        "skill_research_objects",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop skill_research_objects table."""
    op.drop_index("ix_skill_research_objects_user_id", table_name="skill_research_objects")
    op.drop_index("ix_skill_research_objects_skill_id", table_name="skill_research_objects")
    op.drop_table("skill_research_objects")
