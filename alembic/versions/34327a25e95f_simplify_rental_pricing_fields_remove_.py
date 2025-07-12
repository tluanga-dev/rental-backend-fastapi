"""Simplify rental pricing fields - remove rental_price_per_week, rental_price_per_month, min/max_rental_days and rename rental_price_per_day to rental_rate_per_period, add rental_period

Revision ID: 34327a25e95f
Revises: 711db226002a
Create Date: 2025-07-12 14:52:27.730408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34327a25e95f'
down_revision: Union[str, None] = '711db226002a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new rental_period column first
    op.add_column('items', sa.Column('rental_period', sa.String(length=20), nullable=True, default='daily'))
    
    # Set default value for existing records
    op.execute("UPDATE items SET rental_period = 'daily' WHERE rental_period IS NULL")
    
    # Rename rental_price_per_day to rental_rate_per_period
    op.alter_column('items', 'rental_price_per_day', new_column_name='rental_rate_per_period')
    
    # Drop the columns we no longer need
    op.drop_column('items', 'rental_price_per_week')
    op.drop_column('items', 'rental_price_per_month')
    op.drop_column('items', 'minimum_rental_days')
    op.drop_column('items', 'maximum_rental_days')


def downgrade() -> None:
    # Add back the removed columns
    op.add_column('items', sa.Column('rental_price_per_week', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('items', sa.Column('rental_price_per_month', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('items', sa.Column('minimum_rental_days', sa.String(length=10), nullable=True))
    op.add_column('items', sa.Column('maximum_rental_days', sa.String(length=10), nullable=True))
    
    # Rename rental_rate_per_period back to rental_price_per_day
    op.alter_column('items', 'rental_rate_per_period', new_column_name='rental_price_per_day')
    
    # Drop the rental_period column
    op.drop_column('items', 'rental_period')