"""Reorganize transaction models - add missing constraints and indexes

Revision ID: def456789012
Revises: abc123456789
Create Date: 2025-07-14 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'def456789012'
down_revision = 'abc123456789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add any missing indexes or constraints that weren't in the original models
    # Most constraints should already exist from the enhanced transaction models
    
    # Add helpful indexes for rental operations
    try:
        op.create_index('idx_transaction_rental_status_type', 'transaction_headers', 
                       ['current_rental_status', 'transaction_type'])
    except Exception:
        pass  # Index might already exist
    
    try:
        op.create_index('idx_transaction_line_returned_qty', 'transaction_lines', 
                       ['returned_quantity', 'quantity'])
    except Exception:
        pass  # Index might already exist
    
    # Add comment to document the model reorganization
    op.execute("""
        COMMENT ON TABLE transaction_headers IS 
        'Main transaction records - reorganized into transaction_headers.py for better maintainability'
    """)
    
    op.execute("""
        COMMENT ON TABLE transaction_lines IS 
        'Transaction line items - reorganized into transaction_lines.py for better maintainability'
    """)


def downgrade() -> None:
    # Remove the indexes we added
    try:
        op.drop_index('idx_transaction_rental_status_type', table_name='transaction_headers')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_transaction_line_returned_qty', table_name='transaction_lines')
    except Exception:
        pass