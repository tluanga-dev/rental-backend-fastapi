"""Merge item changes and return system

Revision ID: 2527decb7e8f
Revises: 01178976a702, ff234567890b
Create Date: 2025-07-14 22:50:48.729477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2527decb7e8f'
down_revision: Union[str, None] = ('01178976a702', 'ff234567890b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass