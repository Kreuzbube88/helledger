"""fixed_costs: replace recurring_templates + expected_values

Revision ID: 012
Revises: 011
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    bind = op.get_bind()
    res = bind.execute(sa.text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=:t"
    ), {"t": table})
    return res.fetchone() is not None


def upgrade():
    if _table_exists('recurring_templates'):
        op.drop_table('recurring_templates')
    if _table_exists('expected_values'):
        op.drop_table('expected_values')
    if not _table_exists('fixed_costs'):
        op.create_table(
            'fixed_costs',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('household_id', sa.Integer, sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('amount', sa.Numeric(12, 2), nullable=False),
            sa.Column('cost_type', sa.String(20), nullable=False),
            sa.Column('category_id', sa.Integer, sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
            sa.Column('account_id', sa.Integer, sa.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True),
            sa.Column('interval_months', sa.Integer, nullable=False, default=1),
            sa.Column('show_split', sa.Boolean, nullable=False, default=False),
            sa.Column('start_date', sa.Date, nullable=False),
            sa.Column('end_date', sa.Date, nullable=True),
            sa.Column('next_date', sa.Date, nullable=False),
            sa.Column('loan_id', sa.Integer, sa.ForeignKey('loans.id', ondelete='SET NULL'), nullable=True),
            sa.Column('is_active', sa.Boolean, nullable=False, default=True),
            sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        )


def downgrade():
    pass
