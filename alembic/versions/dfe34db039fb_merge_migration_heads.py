"""Merge migration heads

Revision ID: dfe34db039fb
Revises: 92796f60a259, add_delivery_pickup_fields_003, optimize_rental_performance
Create Date: 2025-07-19 10:59:44.069244

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfe34db039fb'
down_revision: Union[str, None] = ('92796f60a259', 'add_delivery_pickup_fields_003', 'optimize_rental_performance')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass