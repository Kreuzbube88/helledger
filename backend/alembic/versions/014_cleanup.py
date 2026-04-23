"""drop net_worth_snapshots table

Revision ID: 014
Revises: 013
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    if "net_worth_snapshots" in tables:
        op.drop_index("ix_nw_household_date", table_name="net_worth_snapshots")
        op.drop_table("net_worth_snapshots")


def downgrade() -> None:
    op.create_table(
        "net_worth_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("household_id", sa.Integer(), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_assets", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_liabilities", sa.Numeric(14, 2), nullable=False),
        sa.Column("net_worth", sa.Numeric(14, 2), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_nw_household_date", "net_worth_snapshots", ["household_id", "snapshot_date"])
