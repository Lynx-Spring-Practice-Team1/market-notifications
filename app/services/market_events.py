from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MarketEvent
from app.schemas.events import MarketEventEnvelope


@dataclass(frozen=True)
class MarketEventRecordResult:
    event: MarketEvent
    created: bool


class MarketEventService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(self, envelope: MarketEventEnvelope) -> MarketEventRecordResult:
        existing = await self.get_event(envelope.payload.event_id)
        if existing is not None:
            return MarketEventRecordResult(event=existing, created=False)

        payload = envelope.payload
        event = MarketEvent(
            event_id=payload.event_id,
            event_type=payload.event_type,
            headline=payload.headline,
            scope=payload.scope,
            target=payload.target,
            magnitude=Decimal(str(payload.magnitude)),
            duration_ticks=payload.duration_ticks,
            market_time=payload.market_time,
            raw_event=envelope.model_dump(mode="json"),
        )
        self.session.add(event)
        await self.session.flush()
        return MarketEventRecordResult(event=event, created=True)

    async def mark_published(self, event: MarketEvent) -> None:
        event.published_at = datetime.now(UTC)
        await self.session.flush()

    async def get_event(self, event_id: str) -> MarketEvent | None:
        return await self.session.scalar(
            select(MarketEvent).where(MarketEvent.event_id == event_id),
        )

    async def list_events(
        self,
        limit: int = 50,
        event_type: str | None = None,
        scope: str | None = None,
        target: str | None = None,
    ) -> list[MarketEvent]:
        statement: Select[tuple[MarketEvent]] = select(MarketEvent)
        if event_type:
            statement = statement.where(MarketEvent.event_type == event_type.strip().upper())
        if scope:
            statement = statement.where(MarketEvent.scope == scope.strip().upper())
        if target:
            statement = statement.where(MarketEvent.target == target.strip())

        statement = statement.order_by(
            MarketEvent.market_time.desc(),
            MarketEvent.received_at.desc(),
        ).limit(limit)
        result = await self.session.scalars(statement)
        return list(result)
