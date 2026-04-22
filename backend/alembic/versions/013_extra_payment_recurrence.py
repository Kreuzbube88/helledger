"""add interval_months and end_date to loan_extra_payments

Revision ID: 013
Revises: 012
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("loan_extra_payments") as batch_op:
        batch_op.add_column(sa.Column("interval_months", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("end_date", sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table("loan_extra_payments") as batch_op:
        batch_op.drop_column("end_date")
        batch_op.drop_column("interval_months")
