"""Add is_rentable and is_saleable boolean fields to Item model

Revision ID: 4ce01fb85512
Revises: 9c8c1026f594
Create Date: 2025-07-12 11:49:42.201616

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ce01fb85512'
down_revision: Union[str, None] = '9c8c1026f594'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_rentable column with default True
    op.add_column('items', sa.Column('is_rentable', sa.Boolean(), nullable=False, default=True, comment='Item can be rented'))
    
    # Add is_saleable column with default False
    op.add_column('items', sa.Column('is_saleable', sa.Boolean(), nullable=False, default=False, comment='Item can be sold'))
    
    # Set default values for existing records
    op.execute("UPDATE items SET is_rentable = TRUE WHERE is_rentable IS NULL")
    op.execute("UPDATE items SET is_saleable = FALSE WHERE is_saleable IS NULL")


def downgrade() -> None:
    # Remove the boolean columns
    op.drop_column('items', 'is_saleable')
    op.drop_column('items', 'is_rentable')