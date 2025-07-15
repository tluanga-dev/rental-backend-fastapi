"""Remove rental fields from TransactionHeader

Revision ID: remove_header_rental_fields_002
Revises: move_rental_fields_001
Create Date: 2025-07-15 04:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'remove_header_rental_fields_002'
down_revision: Union[str, None] = 'move_rental_fields_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove rental fields from TransactionHeader."""
    
    # Step 1: Drop indexes that reference the fields we're removing
    op.execute("DROP INDEX IF EXISTS idx_rental_dates;")
    op.execute("DROP INDEX IF EXISTS idx_rental_status;")
    
    # Step 2: Remove rental fields from transaction_headers (only existing ones)
    op.execute("ALTER TABLE transaction_headers DROP COLUMN IF EXISTS rental_start_date;")
    op.execute("ALTER TABLE transaction_headers DROP COLUMN IF EXISTS rental_end_date;")
    op.execute("ALTER TABLE transaction_headers DROP COLUMN IF EXISTS rental_period;")
    op.execute("ALTER TABLE transaction_headers DROP COLUMN IF EXISTS rental_period_unit;")
    op.execute("ALTER TABLE transaction_headers DROP COLUMN IF EXISTS current_rental_status;")


def downgrade() -> None:
    """Add rental fields back to TransactionHeader."""
    
    # Step 1: Add rental fields back to transaction_headers
    op.add_column('transaction_headers', 
                 sa.Column('rental_start_date', sa.Date(), nullable=True, comment='Rental start date'))
    op.add_column('transaction_headers', 
                 sa.Column('rental_end_date', sa.Date(), nullable=True, comment='Rental end date'))
    op.add_column('transaction_headers', 
                 sa.Column('rental_period', sa.Integer(), nullable=True, comment='Rental period duration'))
    
    # Add rental_period_unit using existing enum
    op.execute("ALTER TABLE transaction_headers ADD COLUMN rental_period_unit rentalperiodunit;")
    op.execute("COMMENT ON COLUMN transaction_headers.rental_period_unit IS 'Rental period unit';")
    
    # Add current_rental_status using existing enum
    op.execute("ALTER TABLE transaction_headers ADD COLUMN current_rental_status rentalstatus;")
    op.execute("COMMENT ON COLUMN transaction_headers.current_rental_status IS 'Current rental status';")
    
    # Step 2: Recreate indexes
    op.create_index('idx_rental_dates', 'transaction_headers', ['rental_start_date', 'rental_end_date'], unique=False)
    op.create_index('idx_rental_status', 'transaction_headers', ['current_rental_status'], unique=False)
    
    # Step 3: Copy data back from transaction_lines to transaction_headers
    # Use the earliest start date and latest end date from lines
    op.execute("""
        WITH rental_aggregates AS (
            SELECT 
                transaction_id,
                MIN(rental_start_date) as min_start_date,
                MAX(rental_end_date) as max_end_date,
                MAX(rental_period) as max_period,
                (array_agg(rental_period_unit ORDER BY line_number))[1] as first_period_unit,
                (array_agg(current_rental_status ORDER BY line_number))[1] as first_status
            FROM transaction_lines 
            WHERE rental_start_date IS NOT NULL OR rental_end_date IS NOT NULL 
               OR current_rental_status IS NOT NULL
            GROUP BY transaction_id
        )
        UPDATE transaction_headers 
        SET 
            rental_start_date = ra.min_start_date,
            rental_end_date = ra.max_end_date,
            rental_period = ra.max_period,
            rental_period_unit = ra.first_period_unit,
            current_rental_status = ra.first_status
        FROM rental_aggregates ra
        WHERE transaction_headers.id = ra.transaction_id
    """)