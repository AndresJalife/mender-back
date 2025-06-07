"""add trigram for matching entity names

Revision ID: 6f26d2f269a1
Revises: 470b99a40eb0
Create Date: 2025-06-07 09:22:21.005858
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6f26d2f269a1'
down_revision: Union[str, None] = '470b99a40eb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# --- helpers -----------------------------------------------------------------
IDX_TITLE_TRGM      = "ix_entity_title_trgm"
IDX_DIRECTOR_TRGM   = "ix_entity_director_trgm"
IDX_ACTOR_NAME_TRGM = "ix_actor_name_trgm"
FN_IMMUTABLE_UNACCENT = "immutable_unaccent"


# --- upgrade -----------------------------------------------------------------
def upgrade() -> None:
    # 1. Required extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    # 2. Create immutable version of unaccent
    op.execute(f"""
        CREATE OR REPLACE FUNCTION {FN_IMMUTABLE_UNACCENT}(text)
        RETURNS text AS
        $$ SELECT unaccent('public.unaccent', $1) $$
        LANGUAGE sql IMMUTABLE;
    """)

    # 3. Trigram indexes using immutable_unaccent
    op.execute(f"""
        CREATE INDEX IF NOT EXISTS {IDX_TITLE_TRGM}
        ON entity
        USING gin ({FN_IMMUTABLE_UNACCENT}(lower(title)) gin_trgm_ops)
    """)

    op.execute(f"""
        CREATE INDEX IF NOT EXISTS {IDX_DIRECTOR_TRGM}
        ON entity
        USING gin ({FN_IMMUTABLE_UNACCENT}(lower(director)) gin_trgm_ops)
    """)

    op.execute(f"""
        CREATE INDEX IF NOT EXISTS {IDX_ACTOR_NAME_TRGM}
        ON actor
        USING gin ({FN_IMMUTABLE_UNACCENT}(lower(name)) gin_trgm_ops)
    """)


# --- downgrade ---------------------------------------------------------------
def downgrade() -> None:
    # 1. Drop trigram indexes
    op.execute(f"DROP INDEX IF EXISTS {IDX_ACTOR_NAME_TRGM}")
    op.execute(f"DROP INDEX IF EXISTS {IDX_DIRECTOR_TRGM}")
    op.execute(f"DROP INDEX IF EXISTS {IDX_TITLE_TRGM}")

    # 2. Drop function (optional, safe to leave if used elsewhere)
    op.execute(f"DROP FUNCTION IF EXISTS {FN_IMMUTABLE_UNACCENT}(text)")

    # 3. Drop extensions (optional)
    op.execute("DROP EXTENSION IF EXISTS unaccent")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
