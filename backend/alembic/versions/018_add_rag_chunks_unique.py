"""add rag chunks uniqueness constraint

Revision ID: 018
Revises: 012
Create Date: 2026-04-20

"""

from alembic import op


revision = "018"
down_revision = "012"
branch_labels = None
depends_on = None


CONSTRAINT_NAME = "uq_rag_chunks_skill_source_chunk"


def upgrade() -> None:
    op.create_unique_constraint(
        CONSTRAINT_NAME,
        "rag_chunks",
        ["skill_id", "source_url", "chunk_index"],
    )


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, "rag_chunks", type_="unique")
