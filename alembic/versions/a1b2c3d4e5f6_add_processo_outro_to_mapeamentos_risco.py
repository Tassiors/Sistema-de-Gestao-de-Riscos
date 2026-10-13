"""add_processo_outro_to_mapeamentos_risco

Revision ID: a1b2c3d4e5f6
Revises: fc9a292db0b9
Create Date: 2026-10-13 16:19:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fc9a292db0b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely check column existence for SQLite compatibility
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('mapeamentos_risco')]
    if 'processo_outro' not in cols:
        op.add_column('mapeamentos_risco', sa.Column('processo_outro', sa.String(length=250), nullable=True))


def downgrade() -> None:
    op.drop_column('mapeamentos_risco', 'processo_outro')
