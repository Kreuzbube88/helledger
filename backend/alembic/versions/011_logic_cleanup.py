"""logic cleanup: drop budgets, drop categories.default_account_id

Revision ID: 011
Revises: 010
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def _col_exists(table: str, col: str) -> bool:
    bind = op.get_bind()
    cols = [r[1] for r in bind.execute(sa.text(f"PRAGMA table_info({table})"))]
    return col in cols


def _table_exists(table: str) -> bool:
    bind = op.get_bind()
    res = bind.execute(sa.text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=:t"
    ), {"t": table})
    return res.fetchone() is not None


def upgrade():
    if _table_exists('budgets'):
        op.drop_table('budgets')
    if _col_exists('categories', 'default_account_id'):
        op.drop_column('categories', 'default_account_id')


def downgrade():
    pass
