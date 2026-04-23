"""add is_savings to categories, to_account_id to fixed_costs

Revision ID: 015
Revises: 014
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("categories") as batch:
        batch.add_column(sa.Column("is_savings", sa.Boolean(), nullable=False, server_default="0"))
    with op.batch_alter_table("fixed_costs") as batch:
        batch.add_column(sa.Column("to_account_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_fc_to_account", "accounts", ["to_account_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("fixed_costs") as batch:
        batch.drop_constraint("fk_fc_to_account", type_="foreignkey")
        batch.drop_column("to_account_id")
    with op.batch_alter_table("categories") as batch:
        batch.drop_column("is_savings")
