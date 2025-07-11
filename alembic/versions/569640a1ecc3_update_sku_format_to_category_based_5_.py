"""Update SKU format to category-based 5-component structure

Revision ID: 569640a1ecc3
Revises: daeaa928ca43
Create Date: 2025-07-12 05:07:15.623109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '569640a1ecc3'
down_revision: Union[str, None] = 'daeaa928ca43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update existing SKU sequences to use new composite key format
    # Clear existing sequences since they use the old format
    op.execute("TRUNCATE TABLE sku_sequences")
    
    # Drop the old unique index since we're changing the key structure
    op.drop_index('idx_sku_sequence_brand_category', table_name='sku_sequences')
    
    # Increase brand_code length to accommodate composite key
    op.alter_column('sku_sequences', 'brand_code',
                    type_=sa.String(50),
                    comment='Composite SKU key in format: CATEGORY-SUBCATEGORY-PRODUCT-ATTRIBUTES')
    
    # Create new unique index on just brand_code (which now holds the composite key)
    op.create_index('idx_sku_sequence_composite_key', 'sku_sequences', ['brand_code'], unique=True)
    
    # Note: Existing SKUs in items table will remain unchanged
    # They can be regenerated using the bulk generation endpoint if needed


def downgrade() -> None:
    # Drop new index
    op.drop_index('idx_sku_sequence_composite_key', table_name='sku_sequences')
    
    # Restore original column type and comment
    op.alter_column('sku_sequences', 'brand_code',
                    type_=sa.String(20),
                    comment='Brand code')
    
    # Restore original unique index
    op.create_index('idx_sku_sequence_brand_category', 'sku_sequences', ['brand_code', 'category_code'], unique=True)
    
    # Clear sequences since they would be in incompatible format
    op.execute("TRUNCATE TABLE sku_sequences")