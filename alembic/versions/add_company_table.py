"""Add company table

Revision ID: add_company_table
Revises: 1826a96f34b8
Create Date: 2025-01-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_company_table'
down_revision: Union[str, None] = '1826a96f34b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create companies table
    op.create_table('companies',
        sa.Column('id', sa.CHAR(36), nullable=False, comment='Primary key'),
        sa.Column('company_name', sa.String(255), nullable=False, comment='Company name'),
        sa.Column('address', sa.Text(), nullable=True, comment='Company address'),
        sa.Column('email', sa.String(255), nullable=True, comment='Company email'),
        sa.Column('phone', sa.String(50), nullable=True, comment='Company phone number'),
        sa.Column('gst_no', sa.String(50), nullable=True, comment='GST registration number'),
        sa.Column('registration_number', sa.String(100), nullable=True, comment='Company registration number'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Soft delete flag'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('created_by', sa.String(255), nullable=True, comment='User who created the record'),
        sa.Column('updated_by', sa.String(255), nullable=True, comment='User who last updated the record'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Soft delete timestamp'),
        sa.Column('deleted_by', sa.String(255), nullable=True, comment='User who deleted the record'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_name'),
        sa.UniqueConstraint('gst_no'),
        sa.UniqueConstraint('registration_number')
    )
    
    # Create indexes
    op.create_index('idx_company_name', 'companies', ['company_name'], unique=False)
    op.create_index('idx_company_name_active', 'companies', ['company_name', 'is_active'], unique=False)
    op.create_index('idx_company_gst_no', 'companies', ['gst_no'], unique=False)
    op.create_index('idx_company_registration_number', 'companies', ['registration_number'], unique=False)
    op.create_index('idx_company_is_active', 'companies', ['is_active'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_company_is_active', table_name='companies')
    op.drop_index('idx_company_registration_number', table_name='companies')
    op.drop_index('idx_company_gst_no', table_name='companies')
    op.drop_index('idx_company_name_active', table_name='companies')
    op.drop_index('idx_company_name', table_name='companies')
    
    # Drop table
    op.drop_table('companies')