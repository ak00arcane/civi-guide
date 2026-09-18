"""add scheme_reports table

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheme_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("scheme_pk", sa.String(length=36), sa.ForeignKey("schemes.id"), nullable=False),
        sa.Column("scheme_id", sa.String(length=64), nullable=False),
        sa.Column("profile_id", sa.String(length=36), sa.ForeignKey("citizen_profiles.id"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("scheme_reports")
