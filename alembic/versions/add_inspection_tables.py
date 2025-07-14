"""Add rental inspection and purchase credit memo tables

Revision ID: add_inspection_tables
Revises: transaction_metadata_table
Create Date: 2024-07-14 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_inspection_tables'
down_revision: Union[str, None] = 'transaction_metadata_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create rental_inspections table
    op.create_table('rental_inspections',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('return_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('inspector_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('inspection_date', sa.DateTime(), nullable=False),
    sa.Column('overall_condition', sa.String(length=20), nullable=False),
    sa.Column('inspection_passed', sa.Boolean(), nullable=False),
    sa.Column('total_repair_cost', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('total_cleaning_cost', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('total_deductions', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('deposit_refund_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('general_notes', sa.Text(), nullable=True),
    sa.Column('customer_notification_required', sa.Boolean(), nullable=False),
    sa.Column('follow_up_actions', sa.JSON(), nullable=True),
    sa.Column('line_inspections', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['inspector_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['return_id'], ['transaction_headers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rental_inspections_return_id'), 'rental_inspections', ['return_id'], unique=False)
    op.create_index(op.f('ix_rental_inspections_inspector_id'), 'rental_inspections', ['inspector_id'], unique=False)
    op.create_index(op.f('ix_rental_inspections_inspection_date'), 'rental_inspections', ['inspection_date'], unique=False)

    # Create purchase_credit_memos table
    op.create_table('purchase_credit_memos',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('return_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('credit_memo_number', sa.String(length=100), nullable=False),
    sa.Column('credit_date', sa.DateTime(), nullable=False),
    sa.Column('credit_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('credit_type', sa.String(length=20), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('exchange_rate', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('line_credits', sa.JSON(), nullable=True),
    sa.Column('credit_terms', sa.String(length=500), nullable=True),
    sa.Column('supplier_notes', sa.Text(), nullable=True),
    sa.Column('received_by', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['received_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['return_id'], ['transaction_headers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('credit_memo_number')
    )
    op.create_index(op.f('ix_purchase_credit_memos_return_id'), 'purchase_credit_memos', ['return_id'], unique=False)
    op.create_index(op.f('ix_purchase_credit_memos_credit_date'), 'purchase_credit_memos', ['credit_date'], unique=False)
    op.create_index(op.f('ix_purchase_credit_memos_received_by'), 'purchase_credit_memos', ['received_by'], unique=False)


def downgrade() -> None:
    # Drop purchase_credit_memos table
    op.drop_index(op.f('ix_purchase_credit_memos_received_by'), table_name='purchase_credit_memos')
    op.drop_index(op.f('ix_purchase_credit_memos_credit_date'), table_name='purchase_credit_memos')
    op.drop_index(op.f('ix_purchase_credit_memos_return_id'), table_name='purchase_credit_memos')
    op.drop_table('purchase_credit_memos')
    
    # Drop rental_inspections table
    op.drop_index(op.f('ix_rental_inspections_inspection_date'), table_name='rental_inspections')
    op.drop_index(op.f('ix_rental_inspections_inspector_id'), table_name='rental_inspections')
    op.drop_index(op.f('ix_rental_inspections_return_id'), table_name='rental_inspections')
    op.drop_table('rental_inspections')