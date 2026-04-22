"""performance indices on transactions

Revision ID: 008
Revises: 007
Create Date: 2026-04-21
"""
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # drop first — SQLite does not roll back DDL, so partial runs leave stale indices
    op.drop_index("ix_tx_household_date", table_name="transactions", if_exists=True)
    op.drop_index("ix_tx_category", table_name="transactions", if_exists=True)
    op.drop_index("ix_tx_account", table_name="transactions", if_exists=True)
    op.drop_index("ix_tx_type", table_name="transactions", if_exists=True)

    op.create_index("ix_tx_household_date", "transactions", ["household_id", "date"])
    op.create_index("ix_tx_category", "transactions", ["category_id"])
    op.create_index("ix_tx_account", "transactions", ["account_id"])
    op.create_index("ix_tx_type", "transactions", ["transaction_type"])


def downgrade() -> None:
    op.drop_index("ix_tx_household_date")
    op.drop_index("ix_tx_category")
    op.drop_index("ix_tx_account")
    op.drop_index("ix_tx_type")
