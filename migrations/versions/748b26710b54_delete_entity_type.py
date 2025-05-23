"""delete entity type

Revision ID: 748b26710b54
Revises: d4ccab65fa77
Create Date: 2025-03-30 19:15:13.021251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '748b26710b54'
down_revision: Union[str, None] = 'd4ccab65fa77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('post', 'entity_type')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post', sa.Column('entity_type', sa.VARCHAR(), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
