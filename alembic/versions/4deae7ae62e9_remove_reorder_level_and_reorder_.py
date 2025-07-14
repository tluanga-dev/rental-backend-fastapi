"""Remove reorder_level and reorder_quantity columns

Revision ID: 4deae7ae62e9
Revises: 1826a96f34b8
Create Date: 2025-07-14 23:11:41.185290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4deae7ae62e9'
down_revision: Union[str, None] = '1826a96f34b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove reorder_level and reorder_quantity columns from items table
    op.drop_column('items', 'reorder_level')
    op.drop_column('items', 'reorder_quantity')


def downgrade() -> None:
    # Add back reorder_level and reorder_quantity columns
    op.add_column('items', sa.Column('reorder_level', sa.String(length=10), nullable=False, server_default='0', comment='Reorder level'))
    op.add_column('items', sa.Column('reorder_quantity', sa.String(length=10), nullable=False, server_default='0', comment='Reorder quantity'))