from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MarketEvent(Base):
    __tablename__ = "market_events"
    __table_args__ = (
        Index("ix_market_events_event_type_market_time", "event_type", "market_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    target: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    magnitude: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    duration_ticks: Mapped[int] = mapped_column(Integer, nullable=False)
    market_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    raw_event: Mapped[dict] = mapped_column(JSON, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
