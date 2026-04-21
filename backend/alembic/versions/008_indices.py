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
    op.create_index("ix_tx_household_date", "transactions", ["household_id", "date"])
    op.create_index("ix_tx_category", "transactions", ["category_id"])
    op.create_index("ix_tx_account", "transactions", ["account_id"])
    op.create_index("ix_tx_type", "transactions", ["type"])


def downgrade() -> None:
    op.drop_index("ix_tx_household_date")
    op.drop_index("ix_tx_category")
    op.drop_index("ix_tx_account")
    op.drop_index("ix_tx_type")
