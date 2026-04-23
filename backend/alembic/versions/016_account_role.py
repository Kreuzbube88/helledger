"""add account_role to accounts

Revision ID: 016
Revises: 015
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("accounts") as batch:
        batch.add_column(sa.Column("account_role", sa.String(50), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("accounts") as batch:
        batch.drop_column("account_role")
