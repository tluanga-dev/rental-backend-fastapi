"""Merge heads

Revision ID: 51e65ebde28e
Revises: 28b39cafd411, add_company_table
Create Date: 2025-07-17 08:38:32.683974

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51e65ebde28e'
down_revision: Union[str, None] = ('28b39cafd411', 'add_company_table')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass