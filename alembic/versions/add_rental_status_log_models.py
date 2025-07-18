"""Add rental status log and lifecycle models

Revision ID: add_rental_status_log
Revises: <previous_revision>
Create Date: 2025-01-18 00:00:00.000000

This migration adds the rental status log table for tracking
historical status changes as defined in the PRD.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_rental_status_log'
down_revision = None  # This should be set to the latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Add rental status log table and related indexes."""
    
    # Create rental_status_logs table
    op.create_table(
        'rental_status_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_line_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rental_lifecycle_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('old_status', sa.String(30), nullable=True),
        sa.Column('new_status', sa.String(30), nullable=False),
        sa.Column('change_reason', sa.String(30), nullable=False),
        sa.Column('change_trigger', sa.String(50), nullable=True),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('system_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('batch_id', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['transaction_id'], ['transaction_headers.id']),
        sa.ForeignKeyConstraint(['transaction_line_id'], ['transaction_lines.id']),
        sa.ForeignKeyConstraint(['rental_lifecycle_id'], ['rental_lifecycles.id']),
        
        # Indexes for performance
        sa.Index('idx_status_log_transaction', 'transaction_id'),
        sa.Index('idx_status_log_line', 'transaction_line_id'),
        sa.Index('idx_status_log_changed_at', 'changed_at'),
        sa.Index('idx_status_log_reason', 'change_reason'),
        sa.Index('idx_status_log_batch', 'batch_id'),
        sa.Index('idx_status_log_system', 'system_generated'),
        
        comment='Historical log of rental status changes for auditing and tracking'
    )
    
    # Add new columns to existing tables if they don't exist
    # (These may already exist from previous migrations)
    
    # Add current_rental_status to transaction_lines if not exists
    try:
        op.add_column('transaction_lines', 
                     sa.Column('current_rental_status', sa.String(30), nullable=True,
                              comment='Current rental status for this line item'))
    except Exception:
        # Column might already exist
        pass
    
    # Create trigger to automatically update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_rental_status_logs_updated_at
        BEFORE UPDATE ON rental_status_logs
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade():
    """Remove rental status log table and related objects."""
    
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS update_rental_status_logs_updated_at ON rental_status_logs;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop table
    op.drop_table('rental_status_logs')
    
    # Remove column from transaction_lines if it was added
    try:
        op.drop_column('transaction_lines', 'current_rental_status')
    except Exception:
        # Column might not exist or might be needed by other features
        pass