"""Add rental lifecycle and return event models

Revision ID: abc123456789
Revises: ff234567890b
Create Date: 2025-07-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abc123456789'
down_revision = 'ff234567890b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to transaction_headers
    op.add_column('transaction_headers', sa.Column('current_rental_status', sa.String(length=30), nullable=True, comment='Current rental status'))
    op.add_column('transaction_headers', sa.Column('customer_advance_balance', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='Customer advance payment balance'))
    
    # Add index for rental status
    op.create_index('idx_rental_status', 'transaction_headers', ['current_rental_status'])
    
    # Create rental_lifecycles table
    op.create_table('rental_lifecycles',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('transaction_id', sa.CHAR(36), nullable=False),
        sa.Column('current_status', sa.String(length=30), nullable=False, comment='Current rental status'),
        sa.Column('last_status_change', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Last status change timestamp'),
        sa.Column('status_changed_by', sa.CHAR(36), nullable=True, comment='User who changed status'),
        sa.Column('total_returned_quantity', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0', comment='Total quantity returned across all events'),
        sa.Column('expected_return_date', sa.Date(), nullable=True, comment='Expected return date (may change with extensions)'),
        sa.Column('total_late_fees', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='Accumulated late fees'),
        sa.Column('total_damage_fees', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='Accumulated damage fees'),
        sa.Column('total_other_fees', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='Other fees (cleaning, restocking, etc.)'),
        sa.Column('notes', sa.Text(), nullable=True, comment='General notes about the rental'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transaction_headers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id')
    )
    
    # Create indexes for rental_lifecycles
    op.create_index('idx_lifecycle_transaction', 'rental_lifecycles', ['transaction_id'])
    op.create_index('idx_lifecycle_status', 'rental_lifecycles', ['current_status'])
    op.create_index('idx_lifecycle_expected_return', 'rental_lifecycles', ['expected_return_date'])
    
    # Create rental_return_events table
    op.create_table('rental_return_events',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('rental_lifecycle_id', sa.CHAR(36), nullable=False, comment='Associated rental lifecycle'),
        sa.Column('event_type', sa.String(length=20), nullable=False, comment='Type of return event'),
        sa.Column('event_date', sa.Date(), nullable=False, comment='Date of the event'),
        sa.Column('processed_by', sa.CHAR(36), nullable=True, comment='User who processed this event'),
        sa.Column('processed_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='When the event was processed'),
        sa.Column('items_returned', sa.JSON(), nullable=True, comment='JSON array of returned items with quantities and conditions'),
        sa.Column('total_quantity_returned', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0', comment='Total quantity returned in this event'),
        sa.Column('late_fees_charged', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='Late fees charged in this event'),
        sa.Column('damage_fees_charged', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='Damage fees charged in this event'),
        sa.Column('other_fees_charged', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='Other fees charged in this event'),
        sa.Column('payment_collected', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='Payment collected during this event'),
        sa.Column('refund_issued', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='Refund issued during this event'),
        sa.Column('new_return_date', sa.Date(), nullable=True, comment='New return date for extensions'),
        sa.Column('extension_reason', sa.String(length=200), nullable=True, comment='Reason for extension'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Notes about this event'),
        sa.Column('receipt_number', sa.String(length=50), nullable=True, comment='Receipt number for payments/refunds'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['rental_lifecycle_id'], ['rental_lifecycles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for rental_return_events
    op.create_index('idx_return_event_lifecycle', 'rental_return_events', ['rental_lifecycle_id'])
    op.create_index('idx_return_event_date', 'rental_return_events', ['event_date'])
    op.create_index('idx_return_event_type', 'rental_return_events', ['event_type'])
    op.create_index('idx_return_event_processed', 'rental_return_events', ['processed_at'])
    
    # Create rental_item_inspections table
    op.create_table('rental_item_inspections',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('return_event_id', sa.CHAR(36), nullable=False, comment='Associated return event'),
        sa.Column('transaction_line_id', sa.CHAR(36), nullable=False, comment='Transaction line being inspected'),
        sa.Column('quantity_inspected', sa.Numeric(precision=10, scale=2), nullable=False, comment='Quantity of this item inspected'),
        sa.Column('condition', sa.String(length=20), nullable=False, comment='Overall condition assessment'),
        sa.Column('inspected_by', sa.CHAR(36), nullable=True, comment='User who performed inspection'),
        sa.Column('inspected_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Inspection timestamp'),
        sa.Column('has_damage', sa.Boolean(), nullable=False, server_default='false', comment='Whether item has damage'),
        sa.Column('damage_description', sa.Text(), nullable=True, comment='Description of any damage'),
        sa.Column('damage_photos', sa.JSON(), nullable=True, comment='JSON array of damage photo URLs'),
        sa.Column('damage_fee_assessed', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='Damage fee assessed for this item'),
        sa.Column('cleaning_fee_assessed', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='Cleaning fee assessed for this item'),
        sa.Column('replacement_required', sa.Boolean(), nullable=False, server_default='false', comment='Whether item needs replacement'),
        sa.Column('replacement_cost', sa.Numeric(precision=15, scale=2), nullable=True, comment='Cost of replacement if required'),
        sa.Column('return_to_stock', sa.Boolean(), nullable=False, server_default='true', comment='Whether item can be returned to stock'),
        sa.Column('stock_location', sa.String(length=100), nullable=True, comment='Where item was returned to stock'),
        sa.Column('inspection_notes', sa.Text(), nullable=True, comment='Detailed inspection notes'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['return_event_id'], ['rental_return_events.id'], ),
        sa.ForeignKeyConstraint(['transaction_line_id'], ['transaction_lines.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for rental_item_inspections
    op.create_index('idx_inspection_return_event', 'rental_item_inspections', ['return_event_id'])
    op.create_index('idx_inspection_transaction_line', 'rental_item_inspections', ['transaction_line_id'])
    op.create_index('idx_inspection_condition', 'rental_item_inspections', ['condition'])
    op.create_index('idx_inspection_damage', 'rental_item_inspections', ['has_damage'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_inspection_damage', table_name='rental_item_inspections')
    op.drop_index('idx_inspection_condition', table_name='rental_item_inspections')
    op.drop_index('idx_inspection_transaction_line', table_name='rental_item_inspections')
    op.drop_index('idx_inspection_return_event', table_name='rental_item_inspections')
    
    op.drop_index('idx_return_event_processed', table_name='rental_return_events')
    op.drop_index('idx_return_event_type', table_name='rental_return_events')
    op.drop_index('idx_return_event_date', table_name='rental_return_events')
    op.drop_index('idx_return_event_lifecycle', table_name='rental_return_events')
    
    op.drop_index('idx_lifecycle_expected_return', table_name='rental_lifecycles')
    op.drop_index('idx_lifecycle_status', table_name='rental_lifecycles')
    op.drop_index('idx_lifecycle_transaction', table_name='rental_lifecycles')
    
    op.drop_index('idx_rental_status', table_name='transaction_headers')
    
    # Drop tables
    op.drop_table('rental_item_inspections')
    op.drop_table('rental_return_events')
    op.drop_table('rental_lifecycles')
    
    # Remove columns from transaction_headers
    op.drop_column('transaction_headers', 'customer_advance_balance')
    op.drop_column('transaction_headers', 'current_rental_status')