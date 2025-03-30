"""entity

Revision ID: 6a8aefbf3a7d
Revises: bde76fab663c
Create Date: 2025-03-30 00:49:50.929917

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a8aefbf3a7d'
down_revision: Union[str, None] = 'bde76fab663c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('entity',
    sa.Column('entity_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('entity_type', sa.String(), nullable=False),
    sa.Column('tmbd_id', sa.Integer(), nullable=True),
    sa.Column('imdb_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('vote_average', sa.Float(), nullable=True),
    sa.Column('release_date', sa.Date, nullable=True),
    sa.Column('revenue', sa.BigInteger(), nullable=True),
    sa.Column('runtime', sa.Integer(), nullable=True),
    sa.Column('budget', sa.BigInteger(), nullable=True),
    sa.Column('original_language', sa.String(), nullable=True),
    sa.Column('overview', sa.String(), nullable=True),
    sa.Column('popularity', sa.Float(), nullable=True),
    sa.Column('tagline', sa.String(), nullable=True),
    sa.Column('trailer', sa.String(), nullable=True),
    sa.Column('director', sa.String(), nullable=True),
    sa.Column('created_date', sa.Date, nullable=True),
    sa.PrimaryKeyConstraint('entity_id')
    )
    op.create_table('watch_provider',
    sa.Column('watch_provider_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('provider_id', sa.Integer(), nullable=False),
    sa.Column('provider_name', sa.String(), nullable=False),
    sa.Column('created_date', sa.Date, nullable=True),
    sa.PrimaryKeyConstraint('watch_provider_id')
    )
    op.create_table('actor',
    sa.Column('actor_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('created_date', sa.Date, nullable=True),
    sa.ForeignKeyConstraint(['entity_id'], ['entity.entity_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('actor_id')
    )
    op.create_table('entity_genre',
    sa.Column('entity_genre_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('created_date', sa.Date, nullable=True),
    sa.ForeignKeyConstraint(['entity_id'], ['entity.entity_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('entity_genre_id')
    )
    op.create_table('entity_production_company',
    sa.Column('entity_production_company_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('created_date', sa.Date, nullable=True),
    sa.ForeignKeyConstraint(['entity_id'], ['entity.entity_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('entity_production_company_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('entity_production_company')
    op.drop_table('entity_genre')
    op.drop_table('actor')
    op.drop_table('watch_provider')
    op.drop_table('entity')
    # ### end Alembic commands ###
