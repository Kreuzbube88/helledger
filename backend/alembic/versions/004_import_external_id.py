"""add external_id to transactions

Revision ID: 004
Revises: 003
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("external_id", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("transactions", "external_id")
