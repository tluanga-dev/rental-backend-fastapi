"""Merge migrations before stock movement tracking

Revision ID: e8eac0a5d19a
Revises: 4deae7ae62e9, def456789012
Create Date: 2025-07-15 01:18:21.693830

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8eac0a5d19a'
down_revision: Union[str, None] = ('4deae7ae62e9', 'def456789012')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass