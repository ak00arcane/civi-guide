"""create civicguide tables

Revision ID: 0001
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables are created via SQLAlchemy metadata.create_all on startup for MVP.
    pass


def downgrade() -> None:
    pass
