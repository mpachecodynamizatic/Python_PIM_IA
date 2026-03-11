"""add_tags_to_product_comments

Revision ID: 7ef0a4369c8d
Revises: 2ae2c7885acd
Create Date: 2026-03-11 19:45:22.247517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ef0a4369c8d'
down_revision: Union[str, None] = '2ae2c7885acd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('product_comments', sa.Column('tags', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('product_comments', 'tags')
