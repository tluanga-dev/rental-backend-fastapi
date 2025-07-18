"""Add performance indexes for rental optimization

Revision ID: optimize_rental_performance
Revises: latest
Create Date: 2024-01-18 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'optimize_rental_performance'
down_revision: Union[str, None] = 'add_rental_status_log'  # Set this to your latest revision
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add performance indexes to optimize rental transaction queries.
    These indexes target the most common query patterns identified in the performance analysis.
    """
    
    # 1. Composite index for stock level lookups (most critical for rental operations)
    op.create_index(
        'idx_stock_levels_item_location_active',
        'stock_levels',
        ['item_id', 'location_id'],
        postgresql_where=sa.text('is_active = true'),
        if_not_exists=True
    )
    
    # 2. Index for transaction lines by transaction_id (for fetching transaction details)
    op.create_index(
        'idx_transaction_lines_transaction_id',
        'transaction_lines',
        ['transaction_id'],
        if_not_exists=True
    )
    
    # 3. Composite index for transaction headers (for filtering and sorting)
    op.create_index(
        'idx_transaction_headers_date_type_status',
        'transaction_headers',
        ['transaction_date', 'transaction_type', 'status'],
        postgresql_where=sa.text("transaction_type = 'RENTAL'"),
        if_not_exists=True
    )
    
    # 4. Index for transaction number lookups (for uniqueness checks)
    op.create_index(
        'idx_transaction_headers_number',
        'transaction_headers',
        ['transaction_number'],
        unique=True,
        if_not_exists=True
    )
    
    # 5. Index for item master rentable items
    op.create_index(
        'idx_items_rentable_active',
        'items',
        ['id'],
        postgresql_where=sa.text('is_rentable = true AND is_active = true'),
        if_not_exists=True
    )
    
    # 6. Index for stock movements by reference
    op.create_index(
        'idx_stock_movements_reference',
        'stock_movements',
        ['reference_type', 'reference_id'],
        if_not_exists=True
    )
    
    # 7. Index for customer lookups
    op.create_index(
        'idx_customers_active',
        'customers',
        ['id'],
        postgresql_where=sa.text('is_active = true'),
        if_not_exists=True
    )
    
    # 8. Covering index for stock levels to avoid table lookups
    op.create_index(
        'idx_stock_levels_covering',
        'stock_levels',
        ['item_id', 'location_id', 'available_quantity', 'on_rent_quantity'],
        postgresql_where=sa.text('is_active = true'),
        if_not_exists=True
    )
    
    # Add table statistics update to help query planner
    op.execute("ANALYZE stock_levels;")
    op.execute("ANALYZE transaction_headers;")
    op.execute("ANALYZE transaction_lines;")
    op.execute("ANALYZE items;")


def downgrade() -> None:
    """
    Remove performance indexes.
    """
    op.drop_index('idx_stock_levels_covering', 'stock_levels', if_exists=True)
    op.drop_index('idx_customers_active', 'customers', if_exists=True)
    op.drop_index('idx_stock_movements_reference', 'stock_movements', if_exists=True)
    op.drop_index('idx_items_rentable_active', 'items', if_exists=True)
    op.drop_index('idx_transaction_headers_number', 'transaction_headers', if_exists=True)
    op.drop_index('idx_transaction_headers_date_type_status', 'transaction_headers', if_exists=True)
    op.drop_index('idx_transaction_lines_transaction_id', 'transaction_lines', if_exists=True)
    op.drop_index('idx_stock_levels_item_location_active', 'stock_levels', if_exists=True)