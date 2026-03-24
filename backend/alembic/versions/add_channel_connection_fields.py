"""add connection fields to channels

Revision ID: 0002_channel_conn
Revises: 0001_export_pref
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_channel_conn'
down_revision = '0001_export_pref'
branch_labels = None
depends_on = None


def upgrade():
    # Add connection_type and connection_config to channels table
    op.execute("""
        ALTER TABLE channels ADD COLUMN connection_type VARCHAR(20)
    """)

    op.execute("""
        ALTER TABLE channels ADD COLUMN connection_config JSON NOT NULL DEFAULT '{}'
    """)


def downgrade():
    # SQLite doesn't support DROP COLUMN easily, so we recreate the table
    op.execute("""
        CREATE TABLE channels_new (
            name VARCHAR(255) NOT NULL,
            code VARCHAR(50) NOT NULL,
            description TEXT,
            active BOOLEAN NOT NULL,
            id VARCHAR(36) PRIMARY KEY,
            created_at DATETIME,
            updated_at DATETIME
        )
    """)

    op.execute("""
        INSERT INTO channels_new (name, code, description, active, id, created_at, updated_at)
        SELECT name, code, description, active, id, created_at, updated_at FROM channels
    """)

    op.execute("DROP TABLE channels")
    op.execute("ALTER TABLE channels_new RENAME TO channels")

    # Recreate indexes
    op.execute("CREATE INDEX ix_channels_name ON channels (name)")
    op.execute("CREATE UNIQUE INDEX ix_channels_code ON channels (code)")
