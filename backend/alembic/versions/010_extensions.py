"""extensions: recurring templates, savings goals, auto-booking fields

Revision ID: 010
Revises: 009
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = '009'
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
    print("DEBUG 010-A: upgrade() entered", flush=True)

    # categories: Konto für Auto-Buchung
    if not _col_exists('categories', 'default_account_id'):
        op.add_column('categories', sa.Column(
            'default_account_id', sa.Integer(),
            sa.ForeignKey('accounts.id', ondelete='SET NULL'),
            nullable=True,
        ))
    print("DEBUG 010-B: categories column ok", flush=True)

    # transactions: Flag für automatisch erstellte Buchungen
    if not _col_exists('transactions', 'is_auto_generated'):
        op.add_column('transactions', sa.Column(
            'is_auto_generated', sa.Boolean(),
            server_default='0', nullable=False,
        ))
    print("DEBUG 010-C: transactions column ok", flush=True)

    # Kreditkonto → Kreditkarte (Wert-Konsistenz)
    op.execute("UPDATE accounts SET account_type = 'credit_card' WHERE account_type = 'credit'")
    print("DEBUG 010-D: account_type update ok", flush=True)

    # Wiederkehrende Vorlagen
    if not _table_exists('recurring_templates'):
        op.create_table(
            'recurring_templates',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('household_id', sa.Integer(),
                      sa.ForeignKey('households.id', ondelete='CASCADE'),
                      nullable=False, index=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('amount', sa.Numeric(12, 2), nullable=False),
            sa.Column('category_id', sa.Integer(),
                      sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
            sa.Column('account_id', sa.Integer(),
                      sa.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True),
            sa.Column('interval', sa.String(20), nullable=False),
            sa.Column('day_of_month', sa.Integer(), server_default='1', nullable=False),
            sa.Column('next_date', sa.Date(), nullable=False),
            sa.Column('show_as_monthly', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    print("DEBUG 010-E: recurring_templates ok", flush=True)

    # Sparziele
    if not _table_exists('savings_goals'):
        op.create_table(
            'savings_goals',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('household_id', sa.Integer(),
                      sa.ForeignKey('households.id', ondelete='CASCADE'),
                      nullable=False, index=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('target_amount', sa.Numeric(12, 2), nullable=False),
            sa.Column('target_date', sa.Date(), nullable=True),
            sa.Column('account_id', sa.Integer(),
                      sa.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True),
            sa.Column('color', sa.String(7), nullable=True),
            sa.Column('notes', sa.String(500), nullable=True),
            sa.Column('is_achieved', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
    print("DEBUG 010-F: savings_goals ok — upgrade() complete", flush=True)


def downgrade():
    op.drop_table('savings_goals')
    op.drop_table('recurring_templates')
    op.execute("UPDATE accounts SET account_type = 'credit' WHERE account_type = 'credit_card'")
    op.drop_column('transactions', 'is_auto_generated')
    op.drop_column('categories', 'default_account_id')
