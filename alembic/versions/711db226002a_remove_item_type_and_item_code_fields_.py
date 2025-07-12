"""Remove item_type and item_code fields from items table

Revision ID: 711db226002a
Revises: 4ce01fb85512
Create Date: 2025-07-12 14:06:36.680620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '711db226002a'
down_revision: Union[str, None] = '4ce01fb85512'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_item_code', table_name='items')
    op.drop_index('idx_item_type', table_name='items')
    
    # Drop columns
    op.drop_column('items', 'item_code')
    op.drop_column('items', 'item_type')


def downgrade() -> None:
    # Add columns back
    op.add_column('items', sa.Column('item_code', sa.String(length=50), nullable=False))
    op.add_column('items', sa.Column('item_type', sa.String(length=20), nullable=False))
    
    # Recreate indexes
    op.create_index('idx_item_code', 'items', ['item_code'])
    op.create_index('idx_item_type', 'items', ['item_type'])
    
    # Create unique constraint for item_code
    op.create_unique_constraint(None, 'items', ['item_code'])