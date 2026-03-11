"""add_is_public_to_saved_views

Revision ID: 2ae2c7885acd
Revises: 48479dbab2a4
Create Date: 2026-03-11 19:35:34.269405

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ae2c7885acd'
down_revision: Union[str, None] = '48479dbab2a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # saved_views: add is_public column
    op.add_column('saved_views', sa.Column('is_public', sa.Boolean(), server_default='0', nullable=False))

    # quality_rules: add scope_category_id (already exists in model, not yet in DB)
    op.add_column('quality_rules', sa.Column('scope_category_id', sa.String(length=36), nullable=True))

    # Note: sync_jobs columns (retry_count etc.) were already applied via create_all
    # Note: product_comments FK drop/recreate is SQLite-incompatible — skipped


def downgrade() -> None:
    op.drop_column('saved_views', 'is_public')
    op.drop_column('quality_rules', 'scope_category_id')
