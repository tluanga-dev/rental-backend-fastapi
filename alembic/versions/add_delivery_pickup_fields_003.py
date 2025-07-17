"""Add delivery and pickup fields to transaction headers

Revision ID: add_delivery_pickup_fields_003
Revises: remove_header_rental_fields_002
Create Date: 2025-07-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_delivery_pickup_fields_003'
down_revision: Union[str, None] = 'remove_header_rental_fields_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add delivery and pickup fields to transaction_headers."""
    
    # Add delivery fields
    op.add_column('transaction_headers', 
                 sa.Column('delivery_required', sa.Boolean(), nullable=False, default=False, 
                          comment='Whether delivery is required for this transaction'))
    op.add_column('transaction_headers', 
                 sa.Column('delivery_address', sa.Text(), nullable=True, 
                          comment='Delivery address if delivery is required'))
    op.add_column('transaction_headers', 
                 sa.Column('delivery_date', sa.Date(), nullable=True, 
                          comment='Scheduled delivery date'))
    op.add_column('transaction_headers', 
                 sa.Column('delivery_time', sa.Time(), nullable=True, 
                          comment='Scheduled delivery time'))
    
    # Add pickup fields
    op.add_column('transaction_headers', 
                 sa.Column('pickup_required', sa.Boolean(), nullable=False, default=False, 
                          comment='Whether pickup is required for this transaction'))
    op.add_column('transaction_headers', 
                 sa.Column('pickup_date', sa.Date(), nullable=True, 
                          comment='Scheduled pickup date'))
    op.add_column('transaction_headers', 
                 sa.Column('pickup_time', sa.Time(), nullable=True, 
                          comment='Scheduled pickup time'))
    
    # Add indexes for efficient queries
    op.create_index('idx_delivery_required', 'transaction_headers', ['delivery_required'], unique=False)
    op.create_index('idx_pickup_required', 'transaction_headers', ['pickup_required'], unique=False)
    op.create_index('idx_delivery_date', 'transaction_headers', ['delivery_date'], unique=False)
    op.create_index('idx_pickup_date', 'transaction_headers', ['pickup_date'], unique=False)


def downgrade() -> None:
    """Remove delivery and pickup fields from transaction_headers."""
    
    # Drop indexes first
    op.drop_index('idx_delivery_required', table_name='transaction_headers')
    op.drop_index('idx_pickup_required', table_name='transaction_headers')
    op.drop_index('idx_delivery_date', table_name='transaction_headers')
    op.drop_index('idx_pickup_date', table_name='transaction_headers')
    
    # Remove columns
    op.drop_column('transaction_headers', 'delivery_required')
    op.drop_column('transaction_headers', 'delivery_address')
    op.drop_column('transaction_headers', 'delivery_date')
    op.drop_column('transaction_headers', 'delivery_time')
    op.drop_column('transaction_headers', 'pickup_required')
    op.drop_column('transaction_headers', 'pickup_date')
    op.drop_column('transaction_headers', 'pickup_time')