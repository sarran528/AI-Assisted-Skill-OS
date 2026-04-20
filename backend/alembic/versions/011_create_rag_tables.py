"""create rag tables

Revision ID: 011
Revises: 010
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rag_chunks",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("skill_id", sa.String(length=64), nullable=False),
        sa.Column("phase", sa.String(length=64), nullable=True),
        sa.Column("technique_id", sa.String(length=64), nullable=True),
        sa.Column("doc_type", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "rag_config",
        sa.Column("id", sa.Integer(), primary_key=True, server_default=sa.text("1")),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("chunk_size", sa.Integer(), nullable=False, server_default=sa.text("512")),
        sa.Column("chunk_overlap", sa.Integer(), nullable=False, server_default=sa.text("64")),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("id = 1", name="rag_config_singleton"),
    )

    op.execute(
        "CREATE INDEX rag_embedding_hnsw_idx ON rag_chunks USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)"
    )
    op.create_index("rag_skill_phase_idx", "rag_chunks", ["skill_id", "phase", "technique_id"])
    op.create_index("rag_doc_type_idx", "rag_chunks", ["doc_type"])


def downgrade() -> None:
    op.drop_index("rag_doc_type_idx", table_name="rag_chunks")
    op.drop_index("rag_skill_phase_idx", table_name="rag_chunks")
    op.execute("DROP INDEX IF EXISTS rag_embedding_hnsw_idx")
    op.drop_table("rag_config")
    op.drop_table("rag_chunks")
