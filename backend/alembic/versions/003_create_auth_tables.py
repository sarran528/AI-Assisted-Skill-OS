"""create auth tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("jti", sa.UUID(), nullable=False, unique=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
    )

    op.create_index("rt_user_id_idx", "refresh_tokens", ["user_id"])
    op.create_index("rt_token_hash_idx", "refresh_tokens", ["token_hash"])
    op.create_index("rt_jti_idx", "refresh_tokens", ["jti"])
    op.create_index("rt_expires_idx", "refresh_tokens", ["expires_at"])

    op.create_table(
        "revoked_access_tokens",
        sa.Column("jti", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index("revoked_access_user_idx", "revoked_access_tokens", ["user_id"])
    op.create_index("revoked_access_expires_idx", "revoked_access_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_index("revoked_access_expires_idx", table_name="revoked_access_tokens")
    op.drop_index("revoked_access_user_idx", table_name="revoked_access_tokens")
    op.drop_table("revoked_access_tokens")

    op.drop_index("rt_expires_idx", table_name="refresh_tokens")
    op.drop_index("rt_jti_idx", table_name="refresh_tokens")
    op.drop_index("rt_token_hash_idx", table_name="refresh_tokens")
    op.drop_index("rt_user_id_idx", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
