"""move connection to sync jobs

Revision ID: move_connection_to_sync_jobs
Revises: 0001_export_pref
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'move_connection_to_sync_jobs'
down_revision = '0001_export_pref'
branch_labels = None
depends_on = None


def upgrade():
    # Add connection fields to sync_jobs table
    op.execute("ALTER TABLE sync_jobs ADD COLUMN connection_type VARCHAR(20)")
    op.execute("ALTER TABLE sync_jobs ADD COLUMN connection_config JSON NOT NULL DEFAULT '{}'")


def downgrade():
    # Remove connection fields from sync_jobs (SQLite doesn't support DROP COLUMN)
    # We need to recreate the table
    op.execute("""
        CREATE TABLE sync_jobs_new (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            channel VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'queued',
            filters JSON NOT NULL DEFAULT '{}',
            started_at DATETIME,
            finished_at DATETIME,
            metrics JSON NOT NULL DEFAULT '{}',
            error_message TEXT,
            retry_count INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL DEFAULT 3,
            next_retry_at DATETIME,
            scheduled BOOLEAN NOT NULL DEFAULT 0,
            cron_expression VARCHAR(100),
            next_run_at DATETIME,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Copy data
    op.execute("""
        INSERT INTO sync_jobs_new (
            id, channel, status, filters, started_at, finished_at, metrics,
            error_message, retry_count, max_retries, next_retry_at, scheduled,
            cron_expression, next_run_at, created_at, updated_at
        )
        SELECT
            id, channel, status, filters, started_at, finished_at, metrics,
            error_message, retry_count, max_retries, next_retry_at, scheduled,
            cron_expression, next_run_at, created_at, updated_at
        FROM sync_jobs
    """)

    op.execute("DROP TABLE sync_jobs")
    op.execute("ALTER TABLE sync_jobs_new RENAME TO sync_jobs")
    op.execute("CREATE INDEX ix_sync_jobs_channel ON sync_jobs (channel)")
