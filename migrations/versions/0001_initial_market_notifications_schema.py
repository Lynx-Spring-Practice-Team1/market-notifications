"""initial market notifications schema

Revision ID: 0001_market_notifications
Revises:
Create Date: 2026-05-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_market_notifications"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "market_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("target", sa.String(length=128), nullable=False),
        sa.Column("magnitude", sa.Numeric(18, 6), nullable=False),
        sa.Column("duration_ticks", sa.Integer(), nullable=False),
        sa.Column("market_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_event", sa.JSON(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_market_events_event_id"), "market_events", ["event_id"], unique=True)
    op.create_index(
        op.f("ix_market_events_event_type"),
        "market_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_market_events_event_type_market_time",
        "market_events",
        ["event_type", "market_time"],
        unique=False,
    )
    op.create_index(
        op.f("ix_market_events_market_time"),
        "market_events",
        ["market_time"],
        unique=False,
    )
    op.create_index(op.f("ix_market_events_scope"), "market_events", ["scope"], unique=False)
    op.create_index(op.f("ix_market_events_target"), "market_events", ["target"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_market_events_target"), table_name="market_events")
    op.drop_index(op.f("ix_market_events_scope"), table_name="market_events")
    op.drop_index(op.f("ix_market_events_market_time"), table_name="market_events")
    op.drop_index("ix_market_events_event_type_market_time", table_name="market_events")
    op.drop_index(op.f("ix_market_events_event_type"), table_name="market_events")
    op.drop_index(op.f("ix_market_events_event_id"), table_name="market_events")
    op.drop_table("market_events")
