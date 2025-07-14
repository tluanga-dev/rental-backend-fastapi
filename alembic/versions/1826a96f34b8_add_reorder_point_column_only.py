"""Add reorder_point column only

Revision ID: 1826a96f34b8
Revises: 628e7b2d9b68
Create Date: 2025-07-14 22:51:19.228123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1826a96f34b8'
down_revision: Union[str, None] = '2527decb7e8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add reorder_point column to items table
    op.add_column('items', sa.Column('reorder_point', sa.Integer(), nullable=False, server_default='0', comment='Reorder point threshold'))
    
    # Remove server_default after column is created
    op.alter_column('items', 'reorder_point', server_default=None)


def downgrade() -> None:
    # Drop reorder_point column
    op.drop_column('items', 'reorder_point')