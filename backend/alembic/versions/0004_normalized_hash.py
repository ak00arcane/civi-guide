"""add raw_snapshots.normalized_hash and backfill it

Revision ID: 0004
Revises: 0003
"""

from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("raw_snapshots", sa.Column("normalized_hash", sa.String(length=64), nullable=True))

    from services.snapshots import normalized_content_hash

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, raw_snapshot_path FROM raw_snapshots")).fetchall()
    for row_id, raw_path in rows:
        content = Path(raw_path).read_bytes()
        conn.execute(
            sa.text("UPDATE raw_snapshots SET normalized_hash = :h WHERE id = :id"),
            {"h": normalized_content_hash(content), "id": row_id},
        )

    with op.batch_alter_table("raw_snapshots") as batch_op:
        batch_op.alter_column("normalized_hash", existing_type=sa.String(length=64), nullable=False)
    op.create_index("ix_raw_snapshots_normalized_hash", "raw_snapshots", ["normalized_hash"])


def downgrade() -> None:
    op.drop_index("ix_raw_snapshots_normalized_hash", table_name="raw_snapshots")
    op.drop_column("raw_snapshots", "normalized_hash")
