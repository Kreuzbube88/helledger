"""loans and loan extra payments

Revision ID: 009
Revises: 008
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "loans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("household_id", sa.Integer(), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("loan_type", sa.String(20), nullable=False),
        sa.Column("lender", sa.String(100), nullable=True),
        sa.Column("principal", sa.Numeric(12, 2), nullable=False),
        sa.Column("interest_rate", sa.Numeric(7, 4), nullable=False),
        sa.Column("monthly_payment", sa.Numeric(12, 2), nullable=False),
        sa.Column("term_months", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("is_existing", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("monthly_extra", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("paid_off_date", sa.Date(), nullable=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("include_in_net_worth", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("purchase_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("equity", sa.Numeric(12, 2), nullable=True),
        sa.Column("property_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("fixed_rate_until", sa.Date(), nullable=True),
        sa.Column("land_charge", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_loans_household_id", "loans", ["household_id"])

    op.create_table(
        "loan_extra_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("loan_id", sa.Integer(), sa.ForeignKey("loans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("effect", sa.String(20), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_loan_ep_loan_id", "loan_extra_payments", ["loan_id"])


def downgrade() -> None:
    op.drop_index("ix_loan_ep_loan_id")
    op.drop_table("loan_extra_payments")
    op.drop_index("ix_loans_household_id")
    op.drop_table("loans")
