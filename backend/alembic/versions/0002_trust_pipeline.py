"""add trust pipeline provenance fields

Revision ID: 0002
Revises: 0001
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("schemes", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("schemes", sa.Column("trust_mode", sa.String(length=32), nullable=False, server_default="unscored"))
    op.add_column("schemes", sa.Column("last_scored_at", sa.DateTime(), nullable=True))

    op.add_column("scheme_sources", sa.Column("source_type", sa.String(length=32), nullable=True))
    op.add_column("scheme_sources", sa.Column("fetched_at", sa.DateTime(), nullable=True))
    op.add_column("scheme_sources", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column("scheme_sources", sa.Column("raw_snapshot_path", sa.String(length=512), nullable=True))

    op.create_table(
        "raw_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("scheme_pk", sa.String(length=36), sa.ForeignKey("schemes.id"), nullable=True),
        sa.Column("source_url", sa.String(length=512), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_snapshot_path", sa.String(length=512), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_raw_snapshots_source_url", "raw_snapshots", ["source_url"])
    op.create_index("ix_raw_snapshots_content_hash", "raw_snapshots", ["content_hash"])


def downgrade() -> None:
    op.drop_index("ix_raw_snapshots_content_hash", table_name="raw_snapshots")
    op.drop_index("ix_raw_snapshots_source_url", table_name="raw_snapshots")
    op.drop_table("raw_snapshots")

    op.drop_column("scheme_sources", "raw_snapshot_path")
    op.drop_column("scheme_sources", "content_hash")
    op.drop_column("scheme_sources", "fetched_at")
    op.drop_column("scheme_sources", "source_type")

    op.drop_column("schemes", "last_scored_at")
    op.drop_column("schemes", "trust_mode")
    op.drop_column("schemes", "confidence")
