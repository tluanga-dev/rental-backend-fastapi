"""Move rental fields from TransactionHeader to TransactionLine

Revision ID: move_rental_fields_001
Revises: stock_movement_001
Create Date: 2025-07-15 04:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'move_rental_fields_001'
down_revision: Union[str, None] = 'stock_movement_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Move rental fields from TransactionHeader to TransactionLine."""
    
    # Step 1: Add the current_rental_status field to TransactionHeader temporarily (if not exists)
    # This allows us to preserve data during migration
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='transaction_headers' AND column_name='current_rental_status') THEN
                ALTER TABLE transaction_headers 
                ADD COLUMN current_rental_status rentalstatus;
                COMMENT ON COLUMN transaction_headers.current_rental_status IS 'Current rental status';
            END IF;
        END $$;
    """)
    
    # Step 2: Add current_rental_status to transaction_lines using existing enum
    op.execute("""
        ALTER TABLE transaction_lines 
        ADD COLUMN current_rental_status rentalstatus;
    """)
    op.execute("COMMENT ON COLUMN transaction_lines.current_rental_status IS 'Current rental status for this item';")
    
    # Step 3: Update rental_period_unit from String to Enum in transaction_lines
    op.execute("""
        ALTER TABLE transaction_lines 
        ALTER COLUMN rental_period_unit TYPE rentalperiodunit 
        USING rental_period_unit::rentalperiodunit;
    """)
    
    # Step 4: Create index for current_rental_status in transaction_lines
    op.create_index('idx_rental_status', 'transaction_lines', ['current_rental_status'], unique=False)
    
    # Step 5: Data migration - copy rental data from TransactionHeader to all its TransactionLines
    # This SQL will copy rental data from headers to lines for all existing transactions
    op.execute("""
        UPDATE transaction_lines 
        SET 
            rental_start_date = th.rental_start_date,
            rental_end_date = th.rental_end_date,
            rental_period = th.rental_period,
            rental_period_unit = th.rental_period_unit::rentalperiodunit,
            current_rental_status = th.current_rental_status::rentalstatus
        FROM transaction_headers th 
        WHERE transaction_lines.transaction_id = th.id 
        AND th.transaction_type = 'RENTAL'
        AND (th.rental_start_date IS NOT NULL OR th.rental_end_date IS NOT NULL OR th.current_rental_status IS NOT NULL)
    """)
    
    # Step 6: Now remove rental fields from TransactionHeader 
    # (we'll do this in a separate migration for safety)


def downgrade() -> None:
    """Revert rental fields move - copy data back to TransactionHeader."""
    
    # Step 1: Copy rental data back from TransactionLine to TransactionHeader
    # For each transaction, use the rental data from the first line item
    op.execute("""
        UPDATE transaction_headers 
        SET 
            rental_start_date = tl.rental_start_date,
            rental_end_date = tl.rental_end_date,
            rental_period = tl.rental_period,
            rental_period_unit = tl.rental_period_unit,
            current_rental_status = tl.current_rental_status
        FROM (
            SELECT DISTINCT ON (transaction_id) 
                transaction_id, rental_start_date, rental_end_date, 
                rental_period, rental_period_unit, current_rental_status
            FROM transaction_lines 
            WHERE rental_start_date IS NOT NULL OR rental_end_date IS NOT NULL 
               OR current_rental_status IS NOT NULL
            ORDER BY transaction_id, line_number
        ) tl
        WHERE transaction_headers.id = tl.transaction_id
    """)
    
    # Step 2: Remove index from transaction_lines
    op.drop_index('idx_rental_status', table_name='transaction_lines')
    
    # Step 3: Revert rental_period_unit back to String in transaction_lines
    op.alter_column('transaction_lines', 'rental_period_unit',
                   existing_type=sa.Enum('HOUR', 'DAY', 'WEEK', 'MONTH', name='rentalperiodunit'),
                   type_=sa.String(length=10),
                   existing_nullable=True)
    
    # Step 4: Remove current_rental_status from transaction_lines
    op.drop_column('transaction_lines', 'current_rental_status')