"""Add transaction metadata table for flexible return storage

Revision ID: transaction_metadata_01
Revises: daeaa928ca43
Create Date: 2025-07-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'transaction_metadata_01'
down_revision = 'daeaa928ca43'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create transaction_metadata table
    op.create_table('transaction_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metadata_type', sa.String(length=50), nullable=False),
        sa.Column('metadata_content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transaction_headers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_transaction_metadata_txn_id', 'transaction_metadata', ['transaction_id'])
    op.create_index('idx_transaction_metadata_type', 'transaction_metadata', ['metadata_type'])
    op.create_index('idx_transaction_metadata_content', 'transaction_metadata', ['metadata_content'], postgresql_using='gin')
    
    # Add return workflow state to transaction_headers if not exists
    op.add_column('transaction_headers', 
        sa.Column('return_workflow_state', sa.String(length=50), nullable=True)
    )
    
    # Add index for return workflow state
    op.create_index('idx_transaction_return_workflow_state', 'transaction_headers', ['return_workflow_state'])
    
    # Create return_reasons lookup table
    op.create_table('return_reasons',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('description', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('requires_inspection', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # Insert common return reasons
    op.execute("""
        INSERT INTO return_reasons (code, description, category, requires_inspection) VALUES
        ('DEFECTIVE', 'Defective Product', 'QUALITY', TRUE),
        ('WRONG_ITEM', 'Wrong Item Received', 'QUALITY', FALSE),
        ('DAMAGED', 'Damaged in Transit', 'QUALITY', TRUE),
        ('NOT_AS_DESCRIBED', 'Not as Described', 'CUSTOMER', FALSE),
        ('CHANGED_MIND', 'Customer Changed Mind', 'CUSTOMER', FALSE),
        ('WRONG_SIZE', 'Wrong Size/Fit', 'CUSTOMER', FALSE),
        ('QUALITY_ISSUE', 'Quality Not Satisfactory', 'SUPPLIER', TRUE),
        ('OVERSTOCK', 'Overstock Return', 'SUPPLIER', FALSE),
        ('EXPIRED', 'Product Expired', 'SUPPLIER', TRUE),
        ('SCHEDULED_RETURN', 'Scheduled Rental Return', 'RENTAL', FALSE),
        ('EARLY_RETURN', 'Early Rental Return', 'RENTAL', FALSE)
    """)
    
    # Add return-specific fields to transaction_lines if not exists
    try:
        op.add_column('transaction_lines',
            sa.Column('return_condition', sa.String(length=1), server_default='A', nullable=True)
        )
    except:
        pass  # Column might already exist
    
    try:
        op.add_column('transaction_lines',
            sa.Column('return_to_stock', sa.Boolean(), server_default='true', nullable=True)
        )
    except:
        pass
    
    try:
        op.add_column('transaction_lines',
            sa.Column('inspection_status', sa.String(length=20), nullable=True)
        )
    except:
        pass
    
    # Create view for sale returns
    op.execute("""
        CREATE OR REPLACE VIEW sale_returns_view AS
        SELECT 
            t.id,
            t.transaction_number,
            t.transaction_date as return_date,
            t.reference_transaction_id as original_transaction_id,
            t.customer_id,
            t.location_id,
            t.status,
            t.total_amount as refund_amount,
            m.metadata_content->>'refund_method' as refund_method,
            m.metadata_content->>'customer_return_method' as return_method,
            m.metadata_content->>'quality_check_required' as quality_check_required,
            m.metadata_content->>'exchange_transaction_id' as exchange_transaction_id,
            (m.metadata_content->>'restocking_fee')::DECIMAL as restocking_fee,
            t.created_at,
            t.updated_at
        FROM transaction_headers t
        JOIN transaction_metadata m ON t.id = m.transaction_id
        WHERE t.transaction_type = 'RETURN'
          AND m.metadata_type = 'RETURN_SALE_RETURN'
    """)
    
    # Create view for purchase returns
    op.execute("""
        CREATE OR REPLACE VIEW purchase_returns_view AS
        SELECT 
            t.id,
            t.transaction_number,
            t.transaction_date as return_date,
            t.reference_transaction_id as original_transaction_id,
            t.customer_id as supplier_id,
            t.location_id,
            t.status,
            m.metadata_content->>'supplier_rma_number' as rma_number,
            m.metadata_content->>'quality_claim' as quality_claim,
            (m.metadata_content->>'expected_credit')::DECIMAL as expected_credit,
            (m.metadata_content->>'expected_credit_date')::DATE as expected_credit_date,
            m.metadata_content->>'credit_memo_number' as credit_memo_number,
            t.created_at,
            t.updated_at
        FROM transaction_headers t
        JOIN transaction_metadata m ON t.id = m.transaction_id
        WHERE t.transaction_type = 'RETURN'
          AND m.metadata_type = 'RETURN_PURCHASE_RETURN'
    """)
    
    # Create view for rental returns
    op.execute("""
        CREATE OR REPLACE VIEW rental_returns_view AS
        SELECT 
            t.id,
            t.transaction_number,
            t.transaction_date as return_date,
            t.reference_transaction_id as original_transaction_id,
            t.customer_id,
            t.location_id,
            t.status,
            (m.metadata_content->>'scheduled_return_date')::DATE as scheduled_return_date,
            (m.metadata_content->>'actual_return_date')::DATE as actual_return_date,
            (m.metadata_content->>'late_fee_amount')::DECIMAL as late_fee,
            (m.metadata_content->>'damage_fee')::DECIMAL as damage_fee,
            (m.metadata_content->>'cleaning_fee')::DECIMAL as cleaning_fee,
            (m.metadata_content->>'deposit_amount')::DECIMAL as deposit_amount,
            (m.metadata_content->>'deposit_refund_amount')::DECIMAL as deposit_refund,
            m.metadata_content->>'damage_assessment_required' as needs_inspection,
            t.created_at,
            t.updated_at
        FROM transaction_headers t
        JOIN transaction_metadata m ON t.id = m.transaction_id
        WHERE t.transaction_type = 'RETURN'
          AND m.metadata_type = 'RETURN_RENTAL_RETURN'
    """)


def downgrade() -> None:
    # Drop views
    op.execute("DROP VIEW IF EXISTS rental_returns_view")
    op.execute("DROP VIEW IF EXISTS purchase_returns_view")
    op.execute("DROP VIEW IF EXISTS sale_returns_view")
    
    # Drop columns from transaction_lines
    op.drop_column('transaction_lines', 'inspection_status')
    op.drop_column('transaction_lines', 'return_to_stock')
    op.drop_column('transaction_lines', 'return_condition')
    
    # Drop return_reasons table
    op.drop_table('return_reasons')
    
    # Drop index and column from transaction_headers
    op.drop_index('idx_transaction_return_workflow_state', table_name='transaction_headers')
    op.drop_column('transaction_headers', 'return_workflow_state')
    
    # Drop indexes from transaction_metadata
    op.drop_index('idx_transaction_metadata_content', table_name='transaction_metadata')
    op.drop_index('idx_transaction_metadata_type', table_name='transaction_metadata')
    op.drop_index('idx_transaction_metadata_txn_id', table_name='transaction_metadata')
    
    # Drop transaction_metadata table
    op.drop_table('transaction_metadata')