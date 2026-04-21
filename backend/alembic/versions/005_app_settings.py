"""add app_settings table

Revision ID: 005
Revises: 004
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.String(500), nullable=False),
    )
    op.execute("INSERT INTO app_settings (key, value) VALUES ('backup_retention_days', '7')")


def downgrade() -> None:
    op.drop_table("app_settings")
