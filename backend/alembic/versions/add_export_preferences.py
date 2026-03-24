"""add export preferences table

Revision ID: 0001_export_pref
Revises: 7ef0a4369c8d
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_export_pref'
down_revision = '7ef0a4369c8d'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS export_preferences (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            resource TEXT NOT NULL,
            selected_fields JSON NOT NULL DEFAULT '[]',
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            CONSTRAINT uq_export_pref_user_resource UNIQUE (user_id, resource)
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_export_preferences_user_id
        ON export_preferences (user_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_export_preferences_resource
        ON export_preferences (resource)
    """)


def downgrade():
    op.drop_table('export_preferences')
