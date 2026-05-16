"""make market_events.target nullable for market-wide events

Revision ID: 0002_market_notifications
Revises: 0001_market_notifications
Create Date: 2026-05-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_market_notifications"
down_revision: str | None = "0001_market_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("market_events", "target", existing_type=sa.String(length=128), nullable=True)


def downgrade() -> None:
    # Set any existing NULLs to empty string before re-adding NOT NULL constraint
    op.execute("UPDATE market_events SET target = '' WHERE target IS NULL")
    op.alter_column("market_events", "target", existing_type=sa.String(length=128), nullable=False)
