"""fix refresh_token ip_address type

Revision ID: 002_fix_refresh_token_ip_address
Revises: 001_initial
Create Date: 2026-04-23 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_fix_refresh_token_ip_address'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert ip_address column from String to INET type for PostgreSQL
    # This will only work on PostgreSQL databases
    try:
        op.execute("ALTER TABLE refresh_tokens ALTER COLUMN ip_address TYPE inet USING ip_address::inet")
    except Exception as e:
        # If the conversion fails, we'll skip it for SQLite compatibility
        print(f"Could not alter ip_address column to inet type: {e}")
        # For SQLite, we'll keep it as String since SQLite doesn't support inet type


def downgrade() -> None:
    # Convert back to String for downgrade
    try:
        op.execute("ALTER TABLE refresh_tokens ALTER COLUMN ip_address TYPE VARCHAR(45)")
    except Exception as e:
        print(f"Could not alter ip_address column back to VARCHAR: {e}")
