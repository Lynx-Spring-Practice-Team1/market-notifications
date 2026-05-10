from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.events import MarketEventEnvelope
from app.services.market_events import MarketEventService


@pytest.mark.asyncio
async def test_record_event_persists_market_event(
    session: AsyncSession,
    market_event_envelope: dict,
) -> None:
    envelope = MarketEventEnvelope.model_validate(market_event_envelope)
    service = MarketEventService(session)

    result = await service.record_event(envelope)
    await session.commit()

    assert result.created is True
    assert result.event.event_id == "evt-001"
    assert result.event.event_type == "SECTOR_SLUMP"
    assert result.event.raw_event["type"] == "MARKET_EVENT"


@pytest.mark.asyncio
async def test_record_event_is_idempotent_for_duplicate_event_id(
    session: AsyncSession,
    market_event_envelope: dict,
) -> None:
    envelope = MarketEventEnvelope.model_validate(market_event_envelope)
    service = MarketEventService(session)

    first = await service.record_event(envelope)
    await session.commit()
    second = await service.record_event(envelope)

    assert first.created is True
    assert second.created is False
    assert second.event.id == first.event.id


@pytest.mark.asyncio
async def test_mark_published_sets_timestamp(
    session: AsyncSession,
    market_event_envelope: dict,
) -> None:
    envelope = MarketEventEnvelope.model_validate(market_event_envelope)
    service = MarketEventService(session)
    result = await service.record_event(envelope)

    await service.mark_published(result.event)

    assert result.event.published_at is not None
    assert result.event.published_at <= datetime.now(UTC)


@pytest.mark.asyncio
async def test_list_events_filters_by_event_type(
    session: AsyncSession,
    market_event_envelope: dict,
) -> None:
    envelope = MarketEventEnvelope.model_validate(market_event_envelope)
    service = MarketEventService(session)
    await service.record_event(envelope)
    await session.commit()

    events = await service.list_events(event_type="sector_slump")

    assert [event.event_id for event in events] == ["evt-001"]
