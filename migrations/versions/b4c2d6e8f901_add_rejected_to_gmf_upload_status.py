"""add rejected to gmf upload status

Revision ID: b4c2d6e8f901
Revises: 9abe85777f15
Create Date: 2026-07-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b4c2d6e8f901"
down_revision: Union[str, Sequence[str], None] = "9abe85777f15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE gmf_upload_status ADD VALUE IF NOT EXISTS 'REJECTED'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL enum values cannot be removed safely without rewriting all
    # dependent columns, so this migration is intentionally irreversible.
    pass
